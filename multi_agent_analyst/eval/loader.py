"""Loaders for evaluation assets."""

from __future__ import annotations

import json
from pathlib import Path

from .contracts import EvalQuestionSet, GoldSet


def load_question_set(path: str) -> EvalQuestionSet:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return EvalQuestionSet(**payload)


def load_gold_set(path: str) -> GoldSet:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return GoldSet(**payload)
