import os

files = {}

files["app/routers/write_photo.py"] = """from fastapi import APIRouter
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
"""

files["app/routers/speaking_practice.py"] = """from fastapi import APIRouter, File, Form, UploadFile
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
"""

files["app/routers/writing_sample.py"] = """from fastapi import APIRouter
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
"""

files["app/routers/speaking_sample.py"] = """from fastapi import APIRouter, File, Form, UploadFile
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
"""

files["artifacts/handoff_3.md"] = """session: 3
files_produced: app/routers/write_photo.py, app/routers/speaking_practice.py, app/routers/writing_sample.py, app/routers/speaking_sample.py
"""

files["artifacts/next.md"] = """session: 4
files: static/index.html, static/css/style.css, static/js/api.js, static/js/recorder.js, static/js/tts.js, static/js/app.js
handoff_out: artifacts/handoff_4.md
is_last: false
read_handoffs: artifacts/handoff_1.md, artifacts/handoff_2.md, artifacts/handoff_3.md
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)