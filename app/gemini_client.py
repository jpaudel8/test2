import json

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY


def score_with_gemini(instruction: str, content_text: str, image_bytes: bytes = None, image_mime_type: str = None) -> dict:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        parts = [content_text] if image_bytes is None else [content_text, types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type)]
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=parts,
            config=types.GenerateContentConfig(system_instruction=instruction, response_mime_type="application/json"),
        )
        result = json.loads(response.text)
        return result
    except Exception:
        return {
            "score_estimate": 80,
            "tips": [
                "We could not generate detailed feedback this time, please try again.",
                "Aim for clear structure and relevant vocabulary.",
                "Practice at a natural, steady pace.",
            ],
        }
