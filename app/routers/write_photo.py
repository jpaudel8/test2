from fastapi import APIRouter
from pydantic import BaseModel
import requests

from app import database, gemini_client, question_bank

router = APIRouter(prefix="/write-photo", tags=["write-photo"])

WRITE_PHOTO_INSTRUCTION = (
    "You are an expert Duolingo English Test (DET) rater grading a 'Write About the Photo' "
    "response. The test-taker was shown an image and asked to describe it in a sentence or two. "
    "Evaluate their written description for how accurately and descriptively it captures the "
    "image, plus grammar, vocabulary, and sentence structure. Return ONLY a JSON object with "
    "exactly two keys: score_estimate (an integer from 10 to 160 on the DET overall-score scale) "
    "and tips (an array of exactly 3 short actionable strings to help the test-taker improve)."
)


class WritePhotoSubmit(BaseModel):
    prompt_id: int
    image_url: str
    description: str


@router.get("/prompt")
def get_prompt():
    return question_bank.get_photo_prompt()


@router.post("/submit")
def submit(body: WritePhotoSubmit):
    image_bytes = None
    image_mime_type = None
    try:
        resp = requests.get(body.image_url, timeout=10)
        resp.raise_for_status()
        image_bytes = resp.content
        image_mime_type = resp.headers.get("Content-Type", "image/jpeg")
    except Exception:
        image_bytes = None
        image_mime_type = None

    result = gemini_client.score_with_gemini(
        instruction=WRITE_PHOTO_INSTRUCTION,
        content_text=body.description,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type,
    )

    detail = dict(result)
    detail["transcript"] = None
    detail["prompt_id"] = body.prompt_id
    database.save_attempt("write_photo", result["score_estimate"] / 160 * 100, detail)

    return {
        "score_estimate": result["score_estimate"],
        "tips": result["tips"],
        "transcript": None,
    }
