"""
FastAPI application — the backend entry point.

Run from the project root:
    uvicorn backend.main:app --reload

Interactive API docs: http://localhost:8000/docs

All endpoints except / and /health require a Google ID token:
    Authorization: Bearer <id_token>
"""

from typing import Dict

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import get_current_user
from backend.config import APP_TITLE, APP_VERSION, GOOGLE_CLIENT_ID, GROQ_API_KEY
from backend.schemas import AnalysisResult, UserProfile
from backend.services.analyzer import analyze_resume
from backend.services.text_extractor import FileError, extract_text
from backend.users import get_or_create_user

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Upload a resume (PDF/DOCX) and optionally a job description to get an ATS score.",
)

# Allow the Streamlit frontend (or any local frontend) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Resume ATS Scorer API is running. Visit /docs for the API documentation."}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "auth_configured": bool(GOOGLE_CLIENT_ID),
        "ai_suggestions_enabled": bool(GROQ_API_KEY),
    }


@app.get("/auth/me", response_model=UserProfile)
def me(user: Dict = Depends(get_current_user)):
    """Called by the frontend right after Google sign-in.
    Registers the user on their first visit (sign up) and returns their profile."""
    profile, is_new_user = get_or_create_user(**user)
    return {**profile, "is_new_user": is_new_user}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(
    resume: UploadFile = File(..., description="Resume file (PDF or DOCX, max 5 MB)"),
    job_description: str = Form("", description="Job description text (optional)"),
    user: Dict = Depends(get_current_user),  # <- only signed-in users can reach this code
):
    file_bytes = await resume.read()

    try:
        resume_text = extract_text(file_bytes, resume.filename)
    except FileError as exc:
        # 400 = the client sent something we can't use; the message is user-friendly.
        raise HTTPException(status_code=400, detail=str(exc))

    return analyze_resume(resume_text, job_description)
