
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "1FurWDiK9A4"

api = YouTubeTranscriptApi()
transcript = api.fetch(video_id)

with open("transcript.txt", "w", encoding="utf-8") as f:
    for snippet in transcript:
        minutes = int(snippet.start // 60)
        seconds = int(snippet.start % 60)

        timestamp = f"[{minutes:02d}:{seconds:02d}]"

        line = f"{timestamp} {snippet.text}\n"

        print(line, end="")
        f.write(line)
