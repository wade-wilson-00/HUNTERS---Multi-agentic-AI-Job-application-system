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

    def add_episodic_memory(self, summary_text: str, metadata: dict = None) -> str:
        """
        Indexes a narrative summary of a conversation episode or session into Chroma DB.
        """
        if not summary_text or not summary_text.strip():
            return ""

        mem_id = f"ep_{uuid.uuid4().hex[:12]}"
        meta = {
            "memory_type": "episodic",
            "timestamp": datetime.datetime.now().isoformat(),
        }
        if metadata:
            meta.update(metadata)

        self.collection.add(
            documents=[summary_text.strip()],
            metadatas=[meta],
            ids=[mem_id]
        )
        return mem_id

    def add_semantic_memory(self, fact_text: str, category: str = "general", metadata: dict = None) -> str:
        """
        Indexes an atomic fact, skill, preference, or goal into Chroma DB.
        """
        if not fact_text or not fact_text.strip():
            return ""

        mem_id = f"sem_{uuid.uuid4().hex[:12]}"
        meta = {
            "memory_type": "semantic",
            "category": category,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        if metadata:
            meta.update(metadata)

        self.collection.add(
            documents=[fact_text.strip()],
            metadatas=[meta],
            ids=[mem_id]
        )
        return mem_id

    def add_memory(self, user_input: str, assistant_response: str, metadata: dict = None):
        """
        Backwards-compatible interface: converts a single turn into an episodic summary.
        """
        if not user_input or not assistant_response:
            return

        summary_text = f"User inquired: {user_input.strip()}\nHunter responded: {assistant_response.strip()}"
        meta = {
            "user_input": user_input[:200],
            "assistant_response": assistant_response[:200]
        }
        if metadata:
            meta.update(metadata)

        return self.add_episodic_memory(summary_text=summary_text, metadata=meta)

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
