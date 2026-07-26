"""
app.py
Streamlit frontend for the AI Interview Agent.

Flow:
  1. Candidate enters name, role, skills, number of questions -> Generate Questions
  2. Candidate answers each question one at a time -> each answer scored immediately
  3. After the last question -> Final Report (strengths, weaknesses, recommendation)
  4. Transcript + result.json saved to outputs/
"""

import os
import json
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from interview import generate_questions
from evaluator import evaluate_answer, generate_final_report

load_dotenv()

st.set_page_config(page_title="AI Interview Agent", page_icon="🧑‍💻", layout="centered")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
defaults = {
    "stage": "setup",       # setup -> interview -> report
    "candidate_name": "",
    "role": "",
    "skills": "",
    "questions": [],
    "current_idx": 0,
    "qa_records": [],       # list of {question, answer, score, verdict, feedback}
    "final_report": None,
    "last_result": None,    # feedback for the just-submitted answer, shown before advancing
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def reset_session():
    for key, val in defaults.items():
        st.session_state[key] = val


st.title("🧑‍💻 AI Interview Agent")
st.caption("Role-specific mock interviews with AI-generated questions and scored feedback.")

# ---------------------------------------------------------------------------
# STAGE 1: Setup
# ---------------------------------------------------------------------------
if st.session_state.stage == "setup":
    st.subheader("Set up your mock interview")

    st.session_state.candidate_name = st.text_input(
        "Candidate Name", value=st.session_state.candidate_name
    )

    role = st.selectbox(
        "Job Role",
        ["Java Developer", "Python Developer", "Data Scientist", "Data Analyst",
         "Frontend Developer", "DevOps Engineer", "Other (type below)"],
    )
    if role == "Other (type below)":
        role = st.text_input("Enter custom role")
    st.session_state.role = role

    st.session_state.skills = st.text_input(
        "Skills (comma-separated)",
        value=st.session_state.skills or "",
        placeholder="e.g. Spring Boot, SQL, Docker",
    )

    num_questions = st.slider("Number of questions", min_value=5, max_value=10, value=5)

    if st.button("Generate Interview Questions", type="primary"):
        if not st.session_state.candidate_name.strip():
            st.warning("Please enter a candidate name.")
        elif not st.session_state.role.strip():
            st.warning("Please select or enter a job role.")
        elif not st.session_state.skills.strip():
            st.warning("Please enter at least one skill.")
        else:
            with st.spinner("Generating questions..."):
                try:
                    questions = generate_questions(
                        st.session_state.role, st.session_state.skills, num_questions
                    )
                    st.session_state.questions = questions
                    st.session_state.current_idx = 0
                    st.session_state.qa_records = []
                    st.session_state.stage = "interview"
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate questions: {e}")

# ---------------------------------------------------------------------------
# STAGE 2: Interview (one question at a time)
# ---------------------------------------------------------------------------
elif st.session_state.stage == "interview":
    idx = st.session_state.current_idx
    total = len(st.session_state.questions)
    q = st.session_state.questions[idx]

    st.subheader(f"Question {idx + 1} of {total}")
    st.progress(idx / total)
    st.markdown(f"**{q['question']}**")

    already_answered = st.session_state.last_result is not None

    answer = st.text_area(
        "Your Answer", key=f"answer_{idx}", height=150, disabled=already_answered
    )

    if not already_answered:
        if st.button("Submit Answer", type="primary"):
            with st.spinner("Evaluating your answer..."):
                try:
                    result = evaluate_answer(st.session_state.role, q["question"], answer)
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")
                    result = {"score": 0, "verdict": "Evaluation error", "feedback": str(e)}

            st.session_state.qa_records.append({
                "question": q["question"],
                "answer": answer,
                "score": result["score"],
                "verdict": result["verdict"],
                "feedback": result["feedback"],
            })
            st.session_state.last_result = result
            st.rerun()
    else:
        result = st.session_state.last_result
        st.info(
            f"**Score: {result['score']}/10** — {result['verdict']}\n\n"
            f"Feedback: {result['feedback']}"
        )

        if idx + 1 < total:
            if st.button("Next Question →", type="primary"):
                st.session_state.current_idx += 1
                st.session_state.last_result = None
                st.rerun()
        else:
            if st.button("Finish & Generate Final Report", type="primary"):
                with st.spinner("Generating final report..."):
                    try:
                        report = generate_final_report(
                            st.session_state.role,
                            st.session_state.skills,
                            st.session_state.qa_records,
                        )
                        st.session_state.final_report = report
                        st.session_state.stage = "report"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate final report: {e}")

# ---------------------------------------------------------------------------
# STAGE 3: Final Report
# ---------------------------------------------------------------------------
elif st.session_state.stage == "report":
    report = st.session_state.final_report
    records = st.session_state.qa_records

    st.subheader(f"Interview Report — {st.session_state.candidate_name}")
    st.markdown(f"**Role:** {st.session_state.role}")
    st.markdown(f"**Skills targeted:** {st.session_state.skills}")

    st.markdown("---")
    for i, r in enumerate(records, start=1):
        st.markdown(f"**Question {i}:** {r['question']}")
        st.markdown(f"Score: **{r['score']}/10** — {r['verdict']}")
        st.caption(r["feedback"])
        st.markdown("")

    st.markdown("---")
    st.markdown(f"### Total Score: {report['total_score']}/{report['max_score']}")
    st.markdown(f"### Overall Rating: {report['overall_rating']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Strengths**")
        for s in report["strengths"]:
            st.markdown(f"✔ {s}")
    with col2:
        st.markdown("**Weaknesses**")
        for w in report["weaknesses"]:
            st.markdown(f"✘ {w}")

    st.markdown("**Recommendation**")
    st.write(report["recommendation"])

    # --- Save transcript + result.json ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = os.path.join(OUTPUT_DIR, f"transcript_{timestamp}.txt")
    result_path = os.path.join(OUTPUT_DIR, f"result_{timestamp}.json")

    with open(transcript_path, "w") as f:
        f.write(f"Candidate: {st.session_state.candidate_name}\n")
        f.write(f"Role: {st.session_state.role}\n")
        f.write(f"Skills: {st.session_state.skills}\n")
        f.write("=" * 60 + "\n\n")
        for i, r in enumerate(records, start=1):
            f.write(f"Question {i}: {r['question']}\n")
            f.write(f"Candidate Answer: {r['answer']}\n")
            f.write(f"Score: {r['score']}/10 ({r['verdict']})\n")
            f.write(f"Feedback: {r['feedback']}\n\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total Score: {report['total_score']}/{report['max_score']}\n")
        f.write(f"Overall Rating: {report['overall_rating']}\n\n")
        f.write("Strengths:\n")
        for s in report["strengths"]:
            f.write(f"  - {s}\n")
        f.write("Weaknesses:\n")
        for w in report["weaknesses"]:
            f.write(f"  - {w}\n")
        f.write(f"\nRecommendation: {report['recommendation']}\n")

    result_json = {
        "candidate_name": st.session_state.candidate_name,
        "role": st.session_state.role,
        "skills": st.session_state.skills,
        "timestamp": timestamp,
        "questions": records,
        "total_score": report["total_score"],
        "max_score": report["max_score"],
        "overall_rating": report["overall_rating"],
        "strengths": report["strengths"],
        "weaknesses": report["weaknesses"],
        "recommendation": report["recommendation"],
    }
    with open(result_path, "w") as f:
        json.dump(result_json, f, indent=2)

    st.success(f"Saved transcript and result to `outputs/`.")

    col1, col2 = st.columns(2)
    with col1:
        with open(transcript_path, "rb") as f:
            st.download_button("⬇ Download Transcript", f, file_name="transcript.txt")
    with col2:
        with open(result_path, "rb") as f:
            st.download_button("⬇ Download Result JSON", f, file_name="result.json")

    if st.button("Start New Interview"):
        reset_session()
        st.rerun()
