import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================
# AI CONFIGURATION
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY not found. "
        "Make sure it is set in your .env file or environment variables."
    )

# ==============================
# KNOWLEDGE BASE CONFIGURATION
# ==============================

KNOWLEDGE_BASE_DIR = "./knowledge_base"
COLLECTION_NAME = "personal_docs"

# ==============================
# RAG CONFIGURATION
# ==============================

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K_RESULTS = 5
