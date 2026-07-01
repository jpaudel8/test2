from fastapi import APIRouter

from app.question_bank import get_listening_item

router = APIRouter(prefix="/interactive-listening", tags=["interactive-listening"])


@router.get("/item")
def get_item():
    return get_listening_item()
