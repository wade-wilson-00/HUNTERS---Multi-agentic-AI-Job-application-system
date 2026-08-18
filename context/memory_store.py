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

    def search_memories(self, query: str, n_results: int = 3) -> str:
        """Searches past long-term memories relevant to the given query."""
        if not query or self.collection.count() == 0:
            return "No previous memories found."

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count())
            )
            
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            
            if not docs:
                return "No relevant memories found."

            formatted = []
            for doc, meta in zip(docs, metas):
                ts = meta.get("timestamp", "Unknown time")[:10]
                formatted.append(f"[{ts}] {doc}")
            
            return "\n\n".join(formatted)
        except Exception as e:
            return f"Error searching memories: {e}"

# Singleton instance
memory_store = MemoryStore()
