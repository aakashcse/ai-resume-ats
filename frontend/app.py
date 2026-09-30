"""
Streamlit frontend for the Resume ATS Scorer.

It can run in two modes:

1. API mode (BACKEND_URL is set, e.g. http://localhost:8000)
   The analysis happens in the FastAPI backend, which this app calls over
   HTTP. The Google ID token is sent with every request and the backend
   verifies it.

2. Standalone mode (BACKEND_URL is NOT set) - used on Streamlit Community Cloud
   Community Cloud runs only one Streamlit app, so this app imports the
   same backend analysis code and runs it directly. There is no public API
   to protect in this mode; the Google sign-in gate below still applies.

Users must sign in with Google first in both modes (see auth_ui.py).

Run from the project root:
    streamlit run frontend/app.py
"""

import os
import sys
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

# Make the project root importable so standalone mode can use the `backend` package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import auth_ui  # noqa: E402

load_dotenv()  # lets you set BACKEND_URL in the .env file
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")  # empty = standalone mode

CATEGORY_LABELS = {
    "sections": "Resume Sections",
    "skills": "Technical Skills",
    "content": "Content Quality",
    "formatting": "Formatting & Contact",
}


# ---------------------------------------------------------------- API call
class SessionExpired(Exception):
    """The backend rejected our Google token (expired or invalid)."""


def analyze_in_process(resume_file, job_description: str) -> dict:
    """Standalone mode: run the backend's analysis code directly (no HTTP)."""
    from backend.services.analyzer import analyze_resume
    from backend.services.text_extractor import FileError, extract_text

    try:
        resume_text = extract_text(resume_file.getvalue(), resume_file.name)
    except FileError as exc:
        raise RuntimeError(str(exc))
    return analyze_resume(resume_text, job_description)


def call_backend(resume_file, job_description: str) -> dict:
    if not BACKEND_URL:
        return analyze_in_process(resume_file, job_description)

    files = {"resume": (resume_file.name, resume_file.getvalue(), resume_file.type)}
    data = {"job_description": job_description}
    headers = {"Authorization": f"Bearer {auth_ui.get_id_token()}"}
    response = requests.post(f"{BACKEND_URL}/analyze", files=files, data=data, headers=headers, timeout=120)

    if response.status_code == 401:
        raise SessionExpired()
    if response.status_code != 200:
        # FastAPI puts error messages in the "detail" field.
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(detail)
    return response.json()


# ---------------------------------------------------------------- UI pieces
def score_color(score: float) -> str:
    if score >= 70:
        return "#16a34a"  # green
    if score >= 55:
        return "#d97706"  # amber
    return "#dc2626"      # red


def show_score_card(result: dict) -> None:
    score = result["ats_score"]
    color = score_color(score)
    st.markdown(
        f"""
        <div style="text-align:center;padding:1.5rem;border-radius:12px;
                    border:2px solid {color};margin-bottom:1rem;">
            <div style="font-size:3.5rem;font-weight:700;color:{color};line-height:1;">{score:.0f}<span style="font-size:1.5rem;">/100</span></div>
            <div style="font-size:1.2rem;font-weight:600;color:{color};margin-top:0.4rem;">{result['rating']}</div>
            <div style="opacity:0.7;margin-top:0.3rem;">Overall ATS Score</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    cols[0].metric("Resume Quality", f"{result['resume_quality_score']:.0f}/100")
    jd = result.get("jd_match")
    cols[1].metric("Job Match", f"{jd['match_score']:.0f}/100" if jd else "—")
    cols[2].metric("Word Count", result["word_count"])


def show_breakdown(result: dict) -> None:
    st.subheader("Score Breakdown")
    for key, category in result["breakdown"].items():
        score, max_score = category["score"], category["max_score"]
        st.markdown(f"**{CATEGORY_LABELS.get(key, key)}** — {score:g} / {max_score:g}")
        st.progress(min(score / max_score, 1.0))
        st.caption(" · ".join(category["details"]))


def show_jd_match(jd: dict) -> None:
    st.subheader("Job Description Match")
    c1, c2 = st.columns(2)
    c1.metric("Skill Coverage", f"{jd['keyword_coverage']:.0f}%")
    c2.metric("Text Similarity", f"{jd['text_similarity']:.0f}%")

    left, right = st.columns(2)
    with left:
        st.markdown("**✅ Matched skills**")
        st.write(", ".join(jd["matched_skills"]) or "None")
    with right:
        st.markdown("**❌ Missing skills**")
        st.write(", ".join(jd["missing_skills"]) or "None — great!")


def show_details(result: dict) -> None:
    left, right = st.columns(2)
    with left:
        st.subheader("Strengths")
        for item in result["strengths"]:
            st.success(item)
    with right:
        st.subheader("Improvements")
        for item in result["improvements"]:
            st.warning(item)

    if result.get("ai_suggestions"):
        st.subheader("AI Suggestions")
        for item in result["ai_suggestions"]:
            st.info(item)

    with st.expander("What the ATS extracted from your resume"):
        st.markdown("**Sections found:** " + (", ".join(result["sections_found"]) or "none"))
        contact = {k: v for k, v in result["contact"].items() if v}
        st.markdown("**Contact info:** " + (", ".join(f"{k}: {v}" for k, v in contact.items()) or "none"))
        st.markdown("**Skills by category:**")
        for category, skills in result["skills_found"].items():
            st.markdown(f"- *{category}:* {', '.join(skills)}")


# ---------------------------------------------------------------- Page
def main() -> None:
    st.set_page_config(page_title="Resume ATS Scorer", page_icon="📄", layout="wide")

    # ---- Authentication gate: nothing below runs unless the user is signed in ----
    if not auth_ui.auth_is_configured():
        auth_ui.show_setup_error()
        return
    if not auth_ui.is_logged_in():
        auth_ui.show_login_page()
        return
    if st.session_state.get("session_expired"):
        auth_ui.show_session_expired()
        return
    try:
        auth_ui.register_user_with_backend(BACKEND_URL)
    except requests.RequestException:
        st.error(
            "The server is still starting up (free hosting sleeps when idle). "
            "Please wait a few seconds and try again."
        )
        if st.button("Try again", type="primary"):
            st.rerun()
        return
    auth_ui.show_account_sidebar()

    st.title("📄 Resume ATS Scorer")
    st.write(
        "Upload your resume to see how an Applicant Tracking System (ATS) might score it. "
        "Add a job description to check how well you match a specific role."
    )

    left, right = st.columns(2)
    with left:
        resume_file = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])
    with right:
        job_description = st.text_area(
            "Job description (optional)",
            height=180,
            placeholder="Paste the job description here to get a match score...",
        )

    if st.button("Analyze Resume", type="primary", disabled=resume_file is None):
        with st.spinner("Analyzing your resume..."):
            try:
                st.session_state["result"] = call_backend(resume_file, job_description)
            except (requests.ConnectionError, requests.Timeout):
                st.error("The server is still starting up. Please wait a few seconds and click Analyze again.")
                return
            except SessionExpired:
                st.session_state["session_expired"] = True
                st.rerun()
            except RuntimeError as exc:
                st.error(f"Analysis failed: {exc}")
                return

    result = st.session_state.get("result")
    if not result:
        st.info("Upload a resume and click **Analyze Resume** to get started.")
        return

    st.divider()
    show_score_card(result)
    show_breakdown(result)
    if result.get("jd_match"):
        st.divider()
        show_jd_match(result["jd_match"])
    st.divider()
    show_details(result)


if __name__ == "__main__":
    main()
