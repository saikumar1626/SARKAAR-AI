from ingestion import DocumentIngestion
from assistant import RAGAssistant
import os

def main_menu():
    """Display main menu and get user choice"""
    print("\n" + "="*50)
    print("🧠 Personal RAG Assistant")
    print("="*50)
    print("\n1. Ingest documents (add to knowledge base)")
    print("2. Ask questions (chat with assistant)")
    print("3. View knowledge base statistics")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    return choice

def ingest_menu():
    """Handle document ingestion"""
    ingestion = DocumentIngestion()
    
    print("\n" + "="*50)
    print("📚 Document Ingestion")
    print("="*50)
    print("\n1. Ingest PDF file")
    print("2. Ingest text file (.txt, .md)")
    print("3. Ingest code file (.py, .js, .java, etc.)")
    print("4. Back to main menu")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "4":
        return
    
    filepath = input("\nEnter the full path to your file: ").strip()
    
    # Remove quotes if user copied path with quotes
    filepath = filepath.strip('"').strip("'")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    tags_input = input("Enter tags (comma-separated, or press Enter to skip): ").strip()
    tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
    
    if choice == "1":
        ingestion.ingest_pdf(filepath, tags)
    elif choice == "2":
        ingestion.ingest_text_file(filepath, tags)
    elif choice == "3":
        ingestion.ingest_code_file(filepath, tags)
    
    input("\nPress Enter to continue...")

def chat_mode():
    """Interactive chat with the assistant"""
    try:
        assistant = RAGAssistant()
    except:
        print("\n❌ Please ingest some documents first!")
        input("\nPress Enter to continue...")
        return
    
    print("\n" + "="*50)
    print("💬 Chat Mode (type 'quit' to exit)")
    print("="*50)
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            continue
        
        assistant.ask(user_input)

def show_stats():
    """Show knowledge base statistics"""
    try:
        ingestion = DocumentIngestion()
        ingestion.get_collection_stats()
    except:
        print("\n❌ Error accessing knowledge base")
    
    input("\nPress Enter to continue...")

def main():
    """Main application loop"""
    print("\n✨ Welcome to your Personal RAG Assistant!")
    print("This tool helps you chat with your documents using AI.\n")
    
    while True:
        choice = main_menu()
        
        if choice == "1":
            ingest_menu()
        elif choice == "2":
            chat_mode()
        elif choice == "3":
            show_stats()
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()