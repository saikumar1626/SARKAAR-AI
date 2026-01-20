import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import os
from datetime import datetime
import uuid
import config


class DocumentIngestion:
    def __init__(self):
        print("🚀 Initializing RAG ingestion system...")

        # Ensure knowledge base directory exists
        os.makedirs(config.KNOWLEDGE_BASE_DIR, exist_ok=True)

        # Initialize ChromaDB (persistent)
        self.client = chromadb.PersistentClient(
            path=config.KNOWLEDGE_BASE_DIR
        )

        # Create or load collection
        try:
            self.collection = self.client.get_collection(
                name=config.COLLECTION_NAME
            )
            print(f"✅ Loaded collection: {config.COLLECTION_NAME}")
        except Exception:
            self.collection = self.client.create_collection(
                name=config.COLLECTION_NAME
            )
            print(f"✅ Created collection: {config.COLLECTION_NAME}")

        # Load embedding model (local, fast, stable)
        print("📥 Loading embedding model...")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model ready")

    # --------------------------------------------------

    def _normalize_text(self, text: str) -> str:
        """Basic cleanup to improve embedding quality"""
        return " ".join(text.replace("\n", " ").split())

    def chunk_text(self, text, chunk_size=None, overlap=None):
        if chunk_size is None:
            chunk_size = config.CHUNK_SIZE
        if overlap is None:
            overlap = config.CHUNK_OVERLAP

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size]).strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    # --------------------------------------------------

    def ingest_pdf(self, filepath, tags=None):
        if tags is None:
            tags = []

        print(f"\n📄 Ingesting PDF: {filepath}")

        try:
            reader = PdfReader(filepath)
            total_chunks = 0

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = self._normalize_text(text)

                if not text:
                    continue

                chunks = self.chunk_text(text)

                for chunk_idx, chunk in enumerate(chunks):
                    embedding = self.embed_model.encode(chunk).tolist()

                    doc_id = str(uuid.uuid4())

                    self.collection.add(
                        ids=[doc_id],
                        documents=[chunk],
                        embeddings=[embedding],
                        metadatas=[{
                            "source": filepath,
                            "page": page_num + 1,
                            "chunk_index": chunk_idx,
                            "document_type": "pdf",
                            "tags": tags,
                            "ingested_at": datetime.utcnow().isoformat()
                        }]
                    )
                    total_chunks += 1

                print(f"  ✓ Page {page_num + 1} ingested")

            print(f"✅ PDF ingestion complete: {total_chunks} chunks")
            return total_chunks

        except Exception as e:
            print(f"❌ PDF ingestion error: {e}")
            return 0

    # --------------------------------------------------

    def ingest_text_file(self, filepath, tags=None):
        if tags is None:
            tags = []

        print(f"\n📝 Ingesting text file: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = self._normalize_text(f.read())

            chunks = self.chunk_text(text)
            total_chunks = 0

            for chunk_idx, chunk in enumerate(chunks):
                embedding = self.embed_model.encode(chunk).tolist()
                doc_id = str(uuid.uuid4())

                self.collection.add(
                    ids=[doc_id],
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "source": filepath,
                        "chunk_index": chunk_idx,
                        "document_type": "text",
                        "tags": tags,
                        "ingested_at": datetime.utcnow().isoformat()
                    }]
                )
                total_chunks += 1

            print(f"✅ Text ingestion complete: {total_chunks} chunks")
            return total_chunks

        except Exception as e:
            print(f"❌ Text ingestion error: {e}")
            return 0

    # --------------------------------------------------

    def ingest_code_file(self, filepath, tags=None):
        if tags is None:
            tags = []

        print(f"\n💻 Ingesting code file: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = self._normalize_text(f.read())

            extension = os.path.splitext(filepath)[1].lstrip(".")
            chunks = self.chunk_text(code, chunk_size=100, overlap=20)
            total_chunks = 0

            for chunk_idx, chunk in enumerate(chunks):
                embedding = self.embed_model.encode(chunk).tolist()
                doc_id = str(uuid.uuid4())

                self.collection.add(
                    ids=[doc_id],
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "source": filepath,
                        "chunk_index": chunk_idx,
                        "document_type": "code",
                        "language": extension,
                        "tags": tags,
                        "ingested_at": datetime.utcnow().isoformat()
                    }]
                )
                total_chunks += 1

            print(f"✅ Code ingestion complete: {total_chunks} chunks")
            return total_chunks

        except Exception as e:
            print(f"❌ Code ingestion error: {e}")
            return 0

    # --------------------------------------------------

    def get_collection_stats(self):
        count = self.collection.count()
        print(f"\n📊 Knowledge Base chunks: {count}")
        return count
