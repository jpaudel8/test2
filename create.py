import os

files = {
    "app/routers/read_select.py": '''from fastapi import APIRouter

from app.question_bank import get_read_select_batch

router = APIRouter(prefix="/read-select", tags=["read-select"])


@router.get("/questions")
def get_questions(count: int = 10):
    items = get_read_select_batch(count)
    return {"items": items}
''',

    "app/routers/read_complete.py": '''from fastapi import APIRouter

from app.question_bank import get_read_complete_batch

router = APIRouter(prefix="/read-complete", tags=["read-complete"])


@router.get("/questions")
def get_questions(count: int = 5):
    items = get_read_complete_batch(count)
    return {"items": items}
''',

    "app/routers/interactive_reading.py": '''from fastapi import APIRouter

from app.question_bank import get_reading_passage

router = APIRouter(prefix="/interactive-reading", tags=["interactive-reading"])


@router.get("/passage")
def get_passage():
    return get_reading_passage()
''',

    "app/routers/interactive_listening.py": '''from fastapi import APIRouter

from app.question_bank import get_listening_item

router = APIRouter(prefix="/interactive-listening", tags=["interactive-listening"])


@router.get("/item")
def get_item():
    return get_listening_item()
''',

    "app/routers/history.py": '''from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_history, get_stats, save_attempt

router = APIRouter(prefix="/history", tags=["history"])


class HistoryLogRequest(BaseModel):
    task_type: str
    score: float
    detail: dict


@router.get("")
def read_history(task_type: Optional[str] = None, limit: int = 50):
    entries = get_history(task_type=task_type, limit=limit)
    return {"entries": entries}


@router.get("/stats")
def read_stats():
    stats = get_stats()
    return {"stats": stats}


@router.post("/log")
def log_history(payload: HistoryLogRequest):
    return save_attempt(payload.task_type, payload.score, payload.detail)
''',

    "artifacts/handoff_2.md": '''session: 2
files_produced: app/routers/read_select.py, app/routers/read_complete.py, app/routers/interactive_reading.py, app/routers/interactive_listening.py, app/routers/history.py
''',

    "artifacts/next.md": '''session: 3
files: app/routers/write_photo.py, app/routers/speaking_practice.py, app/routers/writing_sample.py, app/routers/speaking_sample.py
handoff_out: artifacts/handoff_3.md
is_last: false
read_handoffs: artifacts/handoff_1.md, artifacts/handoff_2.md
''',
}

for path, content in files.items():
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)