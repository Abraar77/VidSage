from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
load_dotenv()

# Persistent database directory
BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_PATH = BASE_DIR / "chroma_db"

# Initialize embedding model
embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)

# Initialize ChromaDB
vector_store = Chroma(
    collection_name="youtube_videos",
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_PATH)
)

conversation_vector_store = Chroma(
    collection_name="conversation_memories",
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_PATH)
)


def store_chunks(chunks, video_id: str):

    ids = [
        f"{video_id}_{index}"
        for index in range(len(chunks))
    ]

    # Attach video ID metadata
    for chunk in chunks:
        chunk.metadata["video_id"] = video_id

    vector_store.add_documents(
        documents=chunks,
        ids=ids
    )

    return len(chunks)

def store_conversation_turn(
    conversation_id: int,
    video_id: str,
    user_message_id: int,
    assistant_message_id: int,
    question: str,
    answer: str
):

    # Combine the question and answer into one document
    content = f"User: {question}\nAssistant: {answer}"

    # Create a LangChain Document
    document = Document(
        page_content=content,
        metadata={
            "conversation_id": conversation_id,
            "video_id": video_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id
        }
    )

    # Unique ID for each conversation turn
    document_id = f"conversation_{conversation_id}_turn_{assistant_message_id}"

    # Store the document in ChromaDB
    conversation_vector_store.add_documents(
        documents=[document],
        ids=[document_id]
    )

    results = conversation_vector_store.get(
    include=["documents", "metadatas"]
)

    print(f"\nchroma result{results}")

    return document_id



def retrieve_conversation_memories(
    query: str,
    conversation_id: int,
    k: int = 5
):
    results = conversation_vector_store.similarity_search(
        query=query,
        k=k,
        filter={
            "conversation_id": conversation_id
        }
    )

    return results
