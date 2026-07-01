from fastapi import APIRouter
from pydantic import BaseModel
import random

from app import database, gemini_client, question_bank

router = APIRouter(prefix="/writing-sample", tags=["writing-sample"])

TIME_LIMIT_SECONDS = 300

WRITING_SAMPLE_INSTRUCTION = (
    "You are an expert Duolingo English Test (DET) rater grading a Writing Sample response, a "
    "timed essay written in response to a prompt. Evaluate the essay for grammar, vocabulary, "
    "coherence, organization, and how well it develops and supports ideas relevant to the prompt. "
    "Return ONLY a JSON object with exactly two keys: score_estimate (an integer from 10 to 160 on "
    "the DET overall-score scale) and tips (an array of exactly 3 short actionable strings)."
)


class WritingSampleSubmit(BaseModel):
    prompt_id: int
    essay: str


@router.get("/prompt")
def get_prompt():
    prompt = random.choice(question_bank.get_writing_sample_prompts())
    return {
        "id": prompt["id"],
        "prompt_text": prompt["prompt_text"],
        "time_limit_seconds": TIME_LIMIT_SECONDS,
    }


@router.post("/submit")
def submit(body: WritingSampleSubmit):
    result = gemini_client.score_with_gemini(
        instruction=WRITING_SAMPLE_INSTRUCTION,
        content_text=body.essay,
    )

    detail = dict(result)
    detail["transcript"] = None
    detail["prompt_id"] = body.prompt_id
    database.save_attempt("writing_sample", result["score_estimate"] / 160 * 100, detail)

    return {
        "score_estimate": result["score_estimate"],
        "tips": result["tips"],
        "transcript": None,
    }
