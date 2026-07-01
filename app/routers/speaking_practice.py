from fastapi import APIRouter, File, Form, UploadFile
import random

from app import database, gemini_client, groq_client, question_bank

router = APIRouter(prefix="/speaking-practice", tags=["speaking-practice"])

SPEAKING_PRACTICE_INSTRUCTION = (
    "You are an expert Duolingo English Test (DET) rater grading a Speaking Practice response. "
    "The test-taker was given a prompt and asked to speak their answer aloud; you are given the "
    "transcript of their spoken response. Evaluate fluency, grammar, vocabulary, coherence, and "
    "how directly the response addresses the prompt. If the transcript is empty or says no speech "
    "was detected, score accordingly and give tips on making sure audio is recorded clearly. "
    "Return ONLY a JSON object with exactly two keys: score_estimate (an integer from 10 to 160 on "
    "the DET overall-score scale) and tips (an array of exactly 3 short actionable strings)."
)


@router.get("/prompt")
def get_prompt():
    return random.choice(question_bank.get_speaking_practice_prompts())


@router.post("/submit")
async def submit(audio: UploadFile = File(...), prompt_id: int = Form(...)):
    audio_bytes = await audio.read()
    transcript = groq_client.transcribe_audio(audio_bytes, filename=audio.filename or "audio.webm")

    content_text = transcript if transcript else "[No speech was detected in the audio recording.]"

    result = gemini_client.score_with_gemini(
        instruction=SPEAKING_PRACTICE_INSTRUCTION,
        content_text=content_text,
    )

    detail = dict(result)
    detail["transcript"] = transcript
    detail["prompt_id"] = prompt_id
    database.save_attempt("speaking_practice", result["score_estimate"] / 160 * 100, detail)

    return {
        "score_estimate": result["score_estimate"],
        "tips": result["tips"],
        "transcript": transcript,
    }
