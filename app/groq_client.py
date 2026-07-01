from groq import Groq

from app.config import GROQ_API_KEY


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
            response_format="json",
            language="en",
        )
        return transcription.text
    except Exception:
        return ""
