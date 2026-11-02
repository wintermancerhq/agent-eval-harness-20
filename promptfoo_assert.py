"""Promptfoo custom Python assertion bridge reusing guardrail.py and run_eval.py."""
from __future__ import annotations
import json
import re
from typing import Any

from guardrail import evaluate_repaired_dispatch
from run_eval import grade_case


def get_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    case = context["vars"]["case"]
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", output.strip(), flags=re.IGNORECASE)
    try:
        candidate_turn = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return {"pass": False, "score": 0.0, "reason": f"Invalid JSON tool turn: {exc}"}

    dispatch = evaluate_repaired_dispatch(candidate_turn, case["session"], case["user_message"])
    passed, detail = grade_case(case, dispatch)
    return {"pass": passed, "score": 1.0 if passed else 0.0, "reason": detail}
