"""
prompts.py
All LLM prompt templates live here so they're easy to tune independently
of the application logic.
"""

QUESTION_GENERATION_PROMPT = """You are a senior technical interviewer conducting a real interview.

Generate {num_questions} interview questions for a candidate applying for the role of "{role}".
Focus the questions on these skills/technologies: {skills}.

Rules:
- Mix difficulty: include some conceptual, some practical/scenario-based, and at least one
  question that probes depth (e.g. "why" or "trade-offs") rather than pure definition recall.
- Questions must be specific to the role and skills given, not generic.
- Do NOT include answers, hints, or numbering prose — only the questions.
- Return STRICT JSON only, no markdown fences, no preamble, in this exact shape:

{{
  "questions": [
    {{"id": 1, "question": "..."}},
    {{"id": 2, "question": "..."}}
  ]
}}
"""

EVALUATION_PROMPT = """You are a strict but fair senior technical interviewer scoring one interview answer.

Role: {role}
Question: {question}
Candidate's Answer: {answer}

Evaluate the answer on technical correctness, completeness, and clarity.

Return STRICT JSON only, no markdown fences, no preamble, in this exact shape:

{{
  "score": <integer 0-10>,
  "verdict": "<one short phrase, e.g. 'Correct but incomplete', 'Excellent', 'Incorrect'>",
  "feedback": "<1-2 sentences on what was missing or what to improve>"
}}

If the answer is empty, off-topic, or "I don't know", score it 0-2 and say so plainly.
"""

FINAL_REPORT_PROMPT = """You are summarizing a completed technical interview.

Role: {role}
Skills targeted: {skills}

Here are all questions, candidate answers, and per-question scores/feedback:
{qa_summary}

Total Score: {total_score}/{max_score}

Based on this, produce STRICT JSON only, no markdown fences, no preamble, in this exact shape:

{{
  "overall_rating": "<one of: Excellent, Good, Average, Needs Improvement, Poor>",
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "recommendation": "<2-3 sentence actionable improvement plan>"
}}

Base strengths/weaknesses on actual topics from the questions above (e.g. specific
technologies or concepts), not generic filler.
"""
