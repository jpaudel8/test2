from fastapi import APIRouter, File, Form, UploadFile
import random

from app import database, gemini_client, groq_client, question_bank

router = APIRouter(prefix="/speaking-sample", tags=["speaking-sample"])

TIME_LIMIT_SECONDS = 90

SPEAKING_SAMPLE_INSTRUCTION = (
    "You are an expert Duolingo English Test (DET) rater grading a Speaking Sample response, a "
    "timed recorded response to a prompt. You are given the transcript of the test-taker's spoken "
    "response. Evaluate fluency, grammar, vocabulary, coherence, and how directly the response "
    "addresses the prompt. If the transcript is empty or says no speech was detected, score "
    "accordingly and give tips on making sure audio is recorded clearly. Return ONLY a JSON object "
    "with exactly two keys: score_estimate (an integer from 10 to 160 on the DET overall-score "
    "scale) and tips (an array of exactly 3 short actionable strings)."
)


@router.get("/prompt")
def get_prompt():
    prompt = random.choice(question_bank.get_speaking_sample_prompts())
    return {
        "id": prompt["id"],
        "prompt_text": prompt["prompt_text"],
        "time_limit_seconds": TIME_LIMIT_SECONDS,
    }


@router.post("/submit")
async def submit(audio: UploadFile = File(...), prompt_id: int = Form(...)):
    audio_bytes = await audio.read()
    transcript = groq_client.transcribe_audio(audio_bytes, filename=audio.filename or "audio.webm")

    content_text = transcript if transcript else "[No speech was detected in the audio recording.]"

    result = gemini_client.score_with_gemini(
        instruction=SPEAKING_SAMPLE_INSTRUCTION,
        content_text=content_text,
    )

    detail = dict(result)
    detail["transcript"] = transcript
    detail["prompt_id"] = prompt_id
    database.save_attempt("speaking_sample", result["score_estimate"] / 160 * 100, detail)

    return {
        "score_estimate": result["score_estimate"],
        "tips": result["tips"],
        "transcript": transcript,
    }
