
import re

from fastapi import APIRouter, HTTPException

from app.schemas.video import VideoRequest
from app.services.transcript import get_transcript
from app.services.text_splitter import split_transcript
from app.services.vector_store import store_chunks

router = APIRouter(
    prefix="/api/video",
    tags=["Video"]
)


def extract_video_id(url: str):
    patterns = [
        r"(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/(?:embed|shorts)/)([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


@router.post("/process")
def process_video(request: VideoRequest):

    video_id = extract_video_id(str(request.url))

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL"
        )

    try:
        transcript = get_transcript(
            video_id,
            request.language
        )
        chunks = split_transcript(transcript)

        total_chunks = store_chunks(
            chunks,
            video_id
        )

        return {
            "message": "video processed sucessfully",
            "video_id": video_id,
            "language": request.language,
            "total_chunks": total_chunks
        }

   
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(error)}"
        )
