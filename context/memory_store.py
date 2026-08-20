"""
context/memory_store.py
Long-term semantic memory storage for Hunter using Chroma DB and BAAI/bge-small-en-v1.5 embeddings.
"""

import os
import uuid
import datetime
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from fastembed import TextEmbedding

import re
from rank_bm25 import BM25Okapi

def _tokenize(text: str) -> list[str]:
    """Helper tokenizer for BM25 sparse search."""
    return re.findall(r"\w+", text.lower())

# Path to local persistent vector database
DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", ".data", "chroma_db")
)
os.makedirs(DATA_DIR, exist_ok=True)

COLLECTION_NAME = "hunter_longterm_memory"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

class BGEEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = TextEmbedding(model_name=model_name)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings_generator = self.model.embed(input)
        return [emb.tolist() for emb in embeddings_generator]

class MemoryStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DATA_DIR)
        self.embedding_fn = BGEEmbeddingFunction(model_name=MODEL_NAME)
        
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    async def add_episodic_memory(
        self,
        session_id: str,
        user_input: str,
        response_text: str,
    ) -> None:
        """s
        Session-Based Episodic Summarization with Upsert.

        On every turn this method:
          1. Queries ChromaDB for an existing summary for this session_id.
          2. If found  → calls hunter_llm to MERGE the new turn into the existing summary.
          3. If absent → calls hunter_llm to generate a fresh summary of the first turn.
          4. Upserts the result under a stable doc ID `ep_{session_id}`,
             so only ONE episodic document exists per session — zero overlap.

        Lazy-imports hunter_llm to avoid circular import at module load time.
        """
        if not user_input or not response_text:
            return

        # ── Lazy import to prevent circular dependency ────────────────────────
        from agents.graphs.groq_llm import hunter_llm

        doc_id = f"ep_{session_id}"
        new_turn_text = (
            f"User: {user_input.strip()}\n"
            f"Hunter: {response_text.strip()}"
        )

        # ── 1. Check for existing session summary ─────────────────────────────
        try:
            existing = self.collection.get(ids=[doc_id])
            existing_docs = existing.get("documents", [])
            existing_summary = existing_docs[0] if existing_docs else None
        except Exception:
            existing_summary = None

        # ── 2. Build the summarization prompt ─────────────────────────────────
        if existing_summary:
            prompt = (
                "You are Hunter's episodic memory manager. Your job is to maintain "
                "a concise, dense narrative summary of an ongoing conversation session.\n\n"
                f"EXISTING SUMMARY:\n{existing_summary}\n\n"
                f"NEW TURN TO INTEGRATE:\n{new_turn_text}\n\n"
                "Update the summary by integrating the new turn naturally. "
                "Preserve all previously mentioned goals, preferences, actions taken, "
                "and outcomes. Do not repeat facts redundantly. Keep it under 120 words. "
                "Output ONLY the updated summary text, nothing else."
            )
        else:
            prompt = (
                "You are Hunter's episodic memory manager. Summarize the following "
                "conversation turn into a concise 2-3 sentence episodic memory. "
                "Capture the user's intent, what Hunter did, and any key outcomes or "
                "preferences mentioned. Keep it under 80 words. "
                "Output ONLY the summary text, nothing else.\n\n"
                f"CONVERSATION TURN:\n{new_turn_text}"
            )

        # ── 3. Call LLM for summarization ─────────────────────────────────────
        try:
            from langchain_core.messages import HumanMessage
            llm_response = await hunter_llm.ainvoke([HumanMessage(content=prompt)])
            summary_text = llm_response.content.strip()
        except Exception as e:
            print(f"[MemoryStore] Warning: LLM summarization failed, falling back to raw text: {e}")
            summary_text = new_turn_text

        if not summary_text:
            return

        # ── 4. Upsert into ChromaDB (stable session-scoped ID) ────────────────
        meta = {
            "memory_type": "episodic",
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.collection.upsert(
            documents=[summary_text],
            metadatas=[meta],
            ids=[doc_id]
        )
        print(f"[MemoryStore] Episodic memory upserted for session '{session_id}'.")

    # ── Private helper: raw ChromaDB write for a single semantic fact ─────────
    def _store_fact(self, fact_text: str, category: str) -> str:
        """Writes one atomic fact into ChromaDB. Called internally by add_semantic_memory."""
        mem_id = f"sem_{uuid.uuid4().hex[:12]}"
        self.collection.add(
            documents=[fact_text.strip()],
            metadatas=[{
                "memory_type": "semantic",
                "category": category,
                "timestamp": datetime.datetime.now().isoformat(),
            }],
            ids=[mem_id]
        )
        return mem_id

    async def add_semantic_memory(self, user_input: str, response_text: str) -> None:
        """
        Gemini 2.5 Flash-powered Semantic Fact Extraction.

        On every turn this method:
          1. Fetches all existing semantic facts from ChromaDB.
          2. Sends existing facts + the current turn to Gemini 2.5 Flash (JSON mode).
          3. Gemini returns {"add_facts": [...], "remove_ids": [...]}
          4. Executes deletions of superseded/contradicted facts.
          5. Writes each new fact via _store_fact().

        Fact categories extracted: skill, target_role, location, preference,
        constraint, experience.

        Gracefully no-ops if Gemini is unavailable or returns malformed JSON.
        """
        if not user_input or not response_text:
            return

        import json
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

        # ── 1. Fetch existing semantic facts ──────────────────────────────────
        existing_facts: list[dict] = []
        try:
            records = self.collection.get(
                where={"memory_type": "semantic"}
            )
            ids   = records.get("ids", [])
            docs  = records.get("documents", [])
            metas = records.get("metadatas", [])
            for mem_id, doc, meta in zip(ids, docs, metas):
                existing_facts.append({
                    "id":       mem_id,
                    "category": meta.get("category", "general"),
                    "text":     doc,
                })
        except Exception as e:
            print(f"[MemoryStore] Warning: Could not fetch existing semantic facts: {e}")

        # ── 2. Build Gemini prompt ─────────────────────────────────────────────
        existing_block = "\n".join(
            f"[{f['id']} | {f['category']}] {f['text']}"
            for f in existing_facts
        ) or "None yet."

        prompt = (
            "You are Hunter's semantic memory manager.\n\n"
            "EXISTING SEMANTIC FACTS:\n"
            f"{existing_block}\n\n"
            "NEW CONVERSATION TURN:\n"
            f"User: {user_input.strip()}\n"
            f"Hunter: {response_text.strip()}\n\n"
            "TASK:\n"
            "Extract facts that are DEFINITIVELY stated (not inferred or assumed).\n"
            "Valid categories: skill, target_role, location, preference, constraint, experience.\n\n"
            "Rules:\n"
            "- add_facts: only genuinely NEW facts not already captured above.\n"
            "- remove_ids: only if this turn CONTRADICTS or fully SUPERSEDES an existing fact.\n"
            "- If nothing new or to remove, return empty lists.\n\n"
            "Return ONLY valid JSON in this exact schema:\n"
            "{\n"
            '  "add_facts": [{"category": "skill", "text": "..."}],\n'
            '  "remove_ids": ["sem_abc123"]\n'
            "}"
        )

        # ── 3. Call Gemini 2.5 Flash in JSON mode ─────────────────────────────
        try:
            model = genai.GenerativeModel(
                model_name="gemini-3.6-flash",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,          # Low temp for deterministic extraction
                    max_output_tokens=512,
                ),
            )
            result = model.generate_content(prompt)
            raw_text = result.text.strip()
            # Clean potential Markdown codeblock wrapping
            if raw_text.startswith("```"):
                first_nl = raw_text.find("\n")
                if first_nl != -1:
                    raw_text = raw_text[first_nl:].strip()
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3].strip()
            
            try:
                extraction = json.loads(raw_text)
                # Handle double-encoded JSON strings returned by the model
                if isinstance(extraction, str):
                    extraction = json.loads(extraction)
            except json.JSONDecodeError as jde:
                print(f"[MemoryStore] JSON parsing failed. Raw response was:\n{raw_text}")
                raise jde
        except Exception as e:
            print(f"[MemoryStore] Warning: Gemini fact extraction failed: {e}")
            return

        # ── 4. Delete superseded facts ─────────────────────────────────────────
        remove_ids = extraction.get("remove_ids", [])
        if remove_ids:
            try:
                self.collection.delete(ids=remove_ids)
                print(f"[MemoryStore] Removed {len(remove_ids)} superseded semantic fact(s).")
            except Exception as e:
                print(f"[MemoryStore] Warning: Could not delete semantic facts: {e}")

        # ── 5. Store new facts ─────────────────────────────────────────────────
        add_facts = extraction.get("add_facts", [])
        for fact in add_facts:
            fact_text = fact.get("text", "").strip()
            category  = fact.get("category", "general")
            if fact_text:
                self._store_fact(fact_text=fact_text, category=category)

        if add_facts:
            print(f"[MemoryStore] Stored {len(add_facts)} new semantic fact(s).")




    def hybrid_search(self, query: str, n_results: int = 4, memory_type: str = None) -> str:
        """
        Executes Hybrid Search combining Dense Vector similarity (BGE-small) 
        and Sparse Keyword matching (BM25Okapi) with Reciprocal Rank Fusion (RRF).
        """
        if not query or self.collection.count() == 0:
            return "No previous memories found."

        try:
            # 1. Fetch collection documents for sparse indexing
            all_records = self.collection.get()
            all_ids = all_records.get("ids", [])
            all_docs = all_records.get("documents", [])
            all_metas = all_records.get("metadatas", [])

            if not all_docs:
                return "No relevant memories found."

            record_map = {
                mem_id: (doc, meta)
                for mem_id, doc, meta in zip(all_ids, all_docs, all_metas)
            }

            # Optional filter by memory_type
            if memory_type:
                filtered_ids = [
                    mem_id for mem_id, (doc, meta) in record_map.items()
                    if meta.get("memory_type") == memory_type
                ]
                if not filtered_ids:
                    return f"No memories found matching type '{memory_type}'."
            else:
                filtered_ids = all_ids

            filtered_docs = [record_map[m_id][0] for m_id in filtered_ids]

            # ── A. Dense Vector Search (ChromaDB) ───────────────────────────
            chroma_where = {"memory_type": memory_type} if memory_type else None
            dense_results = self.collection.query(
                query_texts=[query],
                n_results=min(len(filtered_ids), self.collection.count()),
                where=chroma_where
            )
            dense_ids = dense_results.get("ids", [[]])[0]

            # ── B. Sparse BM25 Search ────────────────────────────────────────
            tokenized_corpus = [_tokenize(doc) for doc in filtered_docs]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = _tokenize(query)

            bm25_scores = bm25.get_scores(tokenized_query)
            ranked_bm25_indices = sorted(
                range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
            )
            sparse_ids = [filtered_ids[i] for i in ranked_bm25_indices if bm25_scores[i] > 0]

            # ── C. Reciprocal Rank Fusion (RRF) ──────────────────────────────
            rrf_scores = {}
            k_constant = 60

            # Rank scores from Dense Search
            for rank, mem_id in enumerate(dense_ids):
                rrf_scores[mem_id] = rrf_scores.get(mem_id, 0.0) + (1.0 / (k_constant + rank + 1))

            # Rank scores from Sparse Search
            for rank, mem_id in enumerate(sparse_ids):
                rrf_scores[mem_id] = rrf_scores.get(mem_id, 0.0) + (1.0 / (k_constant + rank + 1))

            # Sort candidate IDs by final RRF score
            sorted_candidates = sorted(
                rrf_scores.keys(), key=lambda mem_id: rrf_scores[mem_id], reverse=True
            )[:n_results]

            if not sorted_candidates:
                return "No relevant memories found."

            # ── D. Format Output ─────────────────────────────────────────────
            formatted = []
            for mem_id in sorted_candidates:
                doc, meta = record_map[mem_id]
                ts = meta.get("timestamp", "Unknown time")[:10]
                m_type = meta.get("memory_type", "memory").upper()
                cat = meta.get("category", "")
                cat_str = f" ({cat})" if cat else ""

                formatted.append(f"[{ts} | {m_type}{cat_str}] {doc}")

            return "\n\n".join(formatted)

        except Exception as e:
            return f"Error executing hybrid memory search: {e}"

    def search_memories(self, query: str, n_results: int = 4) -> str:
        """Searches long-term memories using Hybrid Search (Dense + BM25 RRF)."""
        return self.hybrid_search(query=query, n_results=n_results)

# Singleton instance
memory_store = MemoryStore()
