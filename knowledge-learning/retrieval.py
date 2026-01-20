import chromadb
from sentence_transformers import SentenceTransformer
import config


class KnowledgeRetrieval:
    def __init__(self):
        print("🔍 Initializing retrieval system...")

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=config.KNOWLEDGE_BASE_DIR
        )

        try:
            self.collection = self.client.get_collection(
                name=config.COLLECTION_NAME
            )
            print("✅ Connected to knowledge base")
        except Exception:
            raise RuntimeError(
                "❌ No knowledge base found. Please ingest documents first."
            )

        # Load embedding model (same as ingestion)
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    # --------------------------------------------------

    def _normalize_query(self, query: str) -> str:
        return " ".join(query.strip().split())

    def query(self, user_query: str, top_k: int = None):
        if top_k is None:
            top_k = config.TOP_K_RESULTS

        user_query = self._normalize_query(user_query)

        print(f"\n🔎 Searching for: '{user_query}'")

        # Generate query embedding
        query_embedding = self.embed_model.encode(user_query).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        context_chunks = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i in range(len(documents)):
            context_chunks.append({
                "content": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i] if distances else None
            })

        if context_chunks:
            print(f"✅ Found {len(context_chunks)} relevant chunks")
        else:
            print("⚠️ No relevant documents found")

        return context_chunks

    # --------------------------------------------------

    def format_context(self, context_chunks):
        if not context_chunks:
            return "No relevant information found in the knowledge base."

        formatted = []

        for i, chunk in enumerate(context_chunks, 1):
            meta = chunk["metadata"]
            source = meta.get("source", "Unknown")
            page = meta.get("page")

            header = f"[Source {i}: {source}"
            if page:
                header += f", Page {page}"
            header += "]"

            formatted.append(
                f"{header}\n{chunk['content']}"
            )

        return "\n\n".join(formatted)
