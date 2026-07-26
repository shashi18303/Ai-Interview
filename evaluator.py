"""
evaluator.py
Scores individual answers and produces the final interview report.
"""

import json
import re
from interview import call_llm
from prompts import EVALUATION_PROMPT, FINAL_REPORT_PROMPT


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _safe_json(raw: str, fallback: dict) -> dict:
    try:
        return json.loads(_strip_json_fences(raw))
    except json.JSONDecodeError:
        return fallback


def evaluate_answer(role: str, question: str, answer: str) -> dict:
    """
    Returns: {"score": int, "verdict": str, "feedback": str}
    """
    if not answer or not answer.strip():
        return {
            "score": 0,
            "verdict": "No answer given",
            "feedback": "Candidate did not provide an answer to this question.",
        }

    prompt = EVALUATION_PROMPT.format(role=role, question=question, answer=answer)
    raw = call_llm(prompt, max_tokens=300)
    result = _safe_json(
        raw,
        fallback={"score": 0, "verdict": "Evaluation failed", "feedback": raw[:200]},
    )

    # Clamp score defensively in case the model ignores bounds
    try:
        result["score"] = max(0, min(10, int(result.get("score", 0))))
    except (TypeError, ValueError):
        result["score"] = 0

    result.setdefault("verdict", "N/A")
    result.setdefault("feedback", "")
    return result


def generate_final_report(role: str, skills: str, qa_records: list[dict]) -> dict:
    """
    qa_records: list of {"question": str, "answer": str, "score": int,
                          "verdict": str, "feedback": str}

    Returns: {"overall_rating": str, "strengths": [...], "weaknesses": [...],
              "recommendation": str, "total_score": int, "max_score": int}
    """
    total_score = sum(r["score"] for r in qa_records)
    max_score = len(qa_records) * 10

    qa_summary_lines = []
    for i, r in enumerate(qa_records, start=1):
        qa_summary_lines.append(
            f"Q{i}: {r['question']}\n"
            f"Answer: {r['answer']}\n"
            f"Score: {r['score']}/10 ({r['verdict']}) - {r['feedback']}\n"
        )
    qa_summary = "\n".join(qa_summary_lines)

    prompt = FINAL_REPORT_PROMPT.format(
        role=role,
        skills=skills,
        qa_summary=qa_summary,
        total_score=total_score,
        max_score=max_score,
    )
    raw = call_llm(prompt, max_tokens=500)
    result = _safe_json(
        raw,
        fallback={
            "overall_rating": _rating_from_score(total_score, max_score),
            "strengths": [],
            "weaknesses": [],
            "recommendation": "Could not generate detailed recommendation; review per-question feedback above.",
        },
    )

    result.setdefault("overall_rating", _rating_from_score(total_score, max_score))
    result.setdefault("strengths", [])
    result.setdefault("weaknesses", [])
    result.setdefault("recommendation", "")
    result["total_score"] = total_score
    result["max_score"] = max_score
    return result


def _rating_from_score(total_score: int, max_score: int) -> str:
    if max_score == 0:
        return "N/A"
    pct = total_score / max_score
    if pct >= 0.85:
        return "Excellent"
    elif pct >= 0.7:
        return "Good"
    elif pct >= 0.5:
        return "Average"
    elif pct >= 0.3:
        return "Needs Improvement"
    else:
        return "Poor"
