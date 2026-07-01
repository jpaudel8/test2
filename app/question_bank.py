import json
import os
import random

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "questions.json")

with open(_DATA_PATH, "r", encoding="utf-8") as _f:
    _DATA = json.load(_f)


def get_read_select_batch(count: int = 10) -> list:
    words = _DATA["read_select_words"]
    n = min(count, len(words))
    return random.sample(words, n)


def get_read_complete_batch(count: int = 5) -> list:
    items = _DATA["read_complete_items"]
    n = min(count, len(items))
    return random.sample(items, n)


def get_reading_passage() -> dict:
    return random.choice(_DATA["reading_passages"])


def get_listening_item() -> dict:
    return random.choice(_DATA["listening_items"])


def get_photo_prompt() -> dict:
    return random.choice(_DATA["photo_prompts"])


def get_speaking_practice_prompts() -> list:
    return _DATA["speaking_practice_prompts"]


def get_writing_sample_prompts() -> list:
    return _DATA["writing_sample_prompts"]


def get_speaking_sample_prompts() -> list:
    return _DATA["speaking_sample_prompts"]
