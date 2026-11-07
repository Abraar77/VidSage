
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.video import router as video_router
from app.routes.chat import router as chat_router


app = FastAPI(
    title="YouTube AI Chatbot API",
    description="Backend API for our YouTube RAG chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)
app.include_router(chat_router)


@app.get("/")
def home():
    return {
        "message": "YouTube AI Chatbot API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
