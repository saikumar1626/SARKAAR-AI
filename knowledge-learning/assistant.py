from openai import OpenAI
from retrieval import KnowledgeRetrieval
import config


class RAGAssistant:
    def __init__(self):
        print("🤖 Initializing AI Assistant (OpenAI)...")

        # Initialize OpenAI client (uses OPENAI_API_KEY automatically)
        self.client = OpenAI()

        # Initialize retrieval system
        self.retrieval = KnowledgeRetrieval()

        print("✅ Assistant ready!\n")

    def ask(self, user_query: str):
        """Ask a question using RAG (Knowledge Base + OpenAI)"""

        # 1️⃣ Retrieve relevant chunks
        context_chunks = self.retrieval.query(user_query)
        context_text = self.retrieval.format_context(context_chunks)

        # 2️⃣ Build messages (correct OpenAI format)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Sarkar, an AI assistant with access to the user's "
                    "personal knowledge base. Answer using the provided context. "
                    "If the context is insufficient, say so clearly."
                )
            },
            {
                "role": "user",
                "content": f"""
Context from knowledge base:
{context_text}

Question:
{user_query}
"""
            }
        ]

        print("\n💭 Thinking...\n")

        # 3️⃣ Call OpenAI (CORRECT)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                temperature=0.3
            )

            answer = response.choices[0].message.content

            print("🤖 Assistant:\n")
            print(answer)
            print("\n" + "=" * 50 + "\n")

            return answer

        except Exception as e:
            print(f"❌ Error calling AI: {e}")
            return None
