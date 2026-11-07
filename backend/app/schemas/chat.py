from pydantic import BaseModel,Field

class ChatRequest(BaseModel):
    video_id: str=Field(description="enter the video id", examples=["1Cbu4yLd5ak"])
    question: str=Field(description="Ask the question about the youtube video ", examples=["summarize the video", "what are the key points about this video?"])
    conversation_id: int | None = None