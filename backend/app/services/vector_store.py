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

    # Unique ID for each conversation turn
    document_id = f"conversation_{conversation_id}_turn_{assistant_message_id}"
    # Create a LangChain Document
    document = Document(
        page_content=content,
        metadata={
            "conversation_id": conversation_id,
            "video_id": video_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "document_id": document_id
        }
    )

    

    # Store the document in ChromaDB
    conversation_vector_store.add_documents(
        documents=[document],
        ids=[document_id]
    )

    results = conversation_vector_store.get(
    include=["documents", "metadatas"]
)

    for index,id in enumerate(results["ids"]):
        print(f"document_id {index}:\n{id}")

    return document_id





def retrieve_conversation_memories(
    query: str,
    conversation_id: int,
    exclude_document_ids: list = None,
    k: int = 5
):
    excluded_ids = set(exclude_document_ids or [])

    # Retrieve a larger, diverse set of candidate memories.
    candidate_docs = conversation_vector_store.max_marginal_relevance_search(
        query=query,
        k=20,
        fetch_k=50,
        lambda_mult=0.5,
        filter={
            "conversation_id": conversation_id
        }
    )

    # Reconstruct document IDs using existing metadata.
    filtered_docs = []

    for doc in candidate_docs:
        assistant_id = doc.metadata.get("assistant_message_id")

        document_id = (
            f"conversation_{conversation_id}_turn_{assistant_id}"
            if assistant_id is not None
            else None
        )

        if document_id not in excluded_ids:
            filtered_docs.append(doc)
    print("MMR candidates:", len(candidate_docs))
    print("Excluded memories:", len(candidate_docs) - len(filtered_docs))
    print("Final memories:", len(filtered_docs))
    return filtered_docs[:k]


