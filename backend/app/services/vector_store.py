from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

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