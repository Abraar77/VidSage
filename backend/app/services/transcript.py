
from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript(video_id: str, language: str = "en"):
    """
    Fetch the transcript of a YouTube video.
    """

    api = YouTubeTranscriptApi()

    transcript_list = api.fetch(
        video_id,
        languages=[language]
    )

    transcript_text = " ".join(
        snippet.text for snippet in transcript_list
    )

    if not transcript_text.strip():
        raise ValueError("Transcript is empty")

    return transcript_text
