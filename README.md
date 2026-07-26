# AI Interview Agent

An AI-powered mock interview tool that generates role-specific technical questions,
scores candidate answers in real time, and produces a final evaluation report with
strengths, weaknesses, and improvement recommendations.

Built to demonstrate: LLM integration, prompt engineering, evaluation/scoring logic,
and multi-step conversational flow.

## Features

- Generates 5–10 interview questions tailored to a job role + skill list
- Candidate answers questions one at a time in a Streamlit UI
- Each answer is scored (0–10) with a verdict and specific feedback, immediately
- Final report: total score, overall rating, strengths, weaknesses, recommendation
- Saves a full transcript (`.txt`) and structured result (`.json`) to `outputs/`
- Swappable LLM backend: Groq (Llama 3, free tier), OpenAI, or Gemini

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **LLM:** Groq (Llama 3) by default — OpenAI GPT and Gemini also supported
- **Evaluation:** Prompt-based scoring (structured JSON responses from the LLM)

## Folder Structure

```
AI-Interview-Agent/
├── app.py            # Streamlit UI and interview flow orchestration
├── interview.py       # LLM client + question generation
├── evaluator.py        # Answer scoring + final report generation
├── prompts.py          # All LLM prompt templates
├── requirements.txt
├── README.md
├── data/
├── outputs/             # transcript_*.txt and result_*.json saved here
└── .env.example
```

## Setup

1. **Clone/copy the project, then install dependencies:**

   ```bash
   cd AI-Interview-Agent
   pip install -r requirements.txt
   ```

   You only need the SDK for the provider you use. If sticking with the default
   (Groq), you can trim `requirements.txt` to just `streamlit`, `python-dotenv`,
   and `groq`.

2. **Get a free API key:**
   - Groq (recommended, free): https://console.groq.com
   - OpenAI: https://platform.openai.com
   - Gemini: https://aistudio.google.com

3. **Configure environment:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and paste your API key. Keep `LLM_PROVIDER=groq` (or switch to
   `openai` / `gemini`).

4. **Run the app:**

   ```bash
   streamlit run app.py
   ```

   This opens the app at `http://localhost:8501`.

## Usage

1. Enter candidate name, select/type a job role, list target skills, pick
   question count (5–10).
2. Click **Generate Interview Questions** — the LLM produces role-specific
   questions.
3. Answer each question in the text box and click **Submit Answer** — you get
   an immediate score (0–10), verdict, and feedback.
4. After the last question, click **Finish & Generate Final Report** for the
   total score, overall rating, strengths, weaknesses, and a recommendation.
5. Download the transcript and JSON result, or find them saved automatically
   under `outputs/`.

## How Scoring Works

Each answer is sent to the LLM with a strict scoring prompt (`prompts.py ->
EVALUATION_PROMPT`) that returns structured JSON: `score` (0–10), `verdict`,
and `feedback`. The final report prompt (`FINAL_REPORT_PROMPT`) receives all
questions/answers/scores together and produces an overall rating plus
role-specific strengths and weaknesses — grounded in the actual topics
covered, not generic filler.

## Extending

- **Persist history across sessions:** add a `data/interviews.db` SQLite table
  and write each completed interview to it from `app.py`.
- **More roles:** the role field accepts free text already — no code change
  needed, the LLM adapts questions to whatever role/skills you give it.
- **Different rubric:** edit `EVALUATION_PROMPT` in `prompts.py` (e.g. weight
  correctness vs. communication differently).
- **Voice input:** swap the `st.text_area` in `app.py` for a speech-to-text
  widget and feed the transcribed text into the same `evaluate_answer()` call.

## Notes

- If the LLM ever returns malformed JSON, both `interview.py` and
  `evaluator.py` handle it gracefully (question generation raises a clear
  error; answer/report scoring falls back to a safe default) rather than
  crashing the app.
- No database is required to run this — SQLite is optional, listed in the
  original spec for future persistence.
