"""
Central configuration for the backend.

Keeping all "magic numbers" in one place makes the scoring logic easy to
explain and easy to tweak without hunting through the code.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # reads a .env file in the project root, if one exists

# ---- App info ----
APP_TITLE = "Resume ATS Scorer API"
APP_VERSION = "1.0.0"

# ---- File upload rules ----
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# ---- Scoring weights (resume quality, total = 100) ----
# Each category is scored out of its own maximum, then added together.
SCORE_WEIGHTS = {
    "sections": 25,     # Does the resume have the standard sections?
    "skills": 20,       # How many recognised technical skills are listed?
    "content": 35,      # Action verbs, numbers/impact, bullet points
    "formatting": 20,   # Contact info, length, ATS-friendly characters
}

# When a job description is given, the final score blends both parts:
#   final = resume_quality * QUALITY_WEIGHT + jd_match * JD_MATCH_WEIGHT
QUALITY_WEIGHT = 0.4
JD_MATCH_WEIGHT = 0.6

# Inside the JD match score:
#   jd_match = keyword_coverage * KEYWORD_WEIGHT + text_similarity * SIMILARITY_WEIGHT
KEYWORD_WEIGHT = 0.7
SIMILARITY_WEIGHT = 0.3

# ---- Resume length (in words) considered ideal for ATS + recruiters ----
IDEAL_MIN_WORDS = 300
IDEAL_MAX_WORDS = 1000

# ---- Authentication (Google Sign-In) ----
# The OAuth Client ID from Google Cloud Console. The backend uses it to check
# that an ID token was issued by Google *for this app* (the token's "aud" claim).
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# SQLite file that stores registered users (created automatically).
DATABASE_PATH = os.getenv("DATABASE_PATH", "users.db")

# ---- Optional AI suggestions (Groq). Leave empty to disable. ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
