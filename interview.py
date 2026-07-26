"""
interview.py
Handles LLM connectivity and interview question generation.

Supports three backends (pick one via LLM_PROVIDER in .env):
  - "groq"   -> free, fast Llama 3 models (recommended default)
  - "openai" -> OpenAI GPT models
  - "gemini" -> Google Gemini models
"""

import os
import json
import re

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


def _strip_json_fences(text: str) -> str:
    """LLMs sometimes wrap JSON in ```json ... ``` even when told not to. Strip it."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """Single entry point for all LLM calls. Returns raw text response."""
    if LLM_PROVIDER == "groq":
        return _call_groq(prompt, max_tokens)
    elif LLM_PROVIDER == "openai":
        return _call_openai(prompt, max_tokens)
    elif LLM_PROVIDER == "gemini":
        return _call_gemini(prompt, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def _call_groq(prompt: str, max_tokens: int) -> str:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.4,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_openai(prompt: str, max_tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.4,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_gemini(prompt: str, max_tokens: int) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(
        prompt,
        generation_config={"max_output_tokens": max_tokens, "temperature": 0.4},
    )
    return resp.text


def generate_questions(role: str, skills: str, num_questions: int = 5) -> list[dict]:
    """
    Returns a list of dicts: [{"id": 1, "question": "..."}, ...]
    Raises ValueError if the LLM response can't be parsed.
    """
    from prompts import QUESTION_GENERATION_PROMPT

    prompt = QUESTION_GENERATION_PROMPT.format(
        num_questions=num_questions, role=role, skills=skills
    )
    raw = call_llm(prompt, max_tokens=800)
    cleaned = _strip_json_fences(raw)

    try:
        data = json.loads(cleaned)
        questions = data["questions"]
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("Empty question list")
        return questions
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Could not parse questions from LLM response: {e}\nRaw: {raw}")
