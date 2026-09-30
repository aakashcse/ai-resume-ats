"""
Pydantic models describing the JSON the API returns.

FastAPI uses these to validate the response and to auto-generate the
interactive docs at http://localhost:8000/docs.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


class CategoryScore(BaseModel):
    score: float        # points earned
    max_score: float    # points available
    details: List[str]  # short notes explaining how the points were given


class JDMatch(BaseModel):
    match_score: float           # 0-100
    keyword_coverage: float      # 0-100, % of JD skills found in resume
    text_similarity: float       # 0-100, TF-IDF cosine similarity
    matched_skills: List[str]
    missing_skills: List[str]


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class AnalysisResult(BaseModel):
    ats_score: float                      # final score, 0-100
    rating: str                           # "Excellent", "Good", ...
    resume_quality_score: float           # 0-100, independent of any JD
    breakdown: Dict[str, CategoryScore]   # sections / skills / content / formatting
    jd_match: Optional[JDMatch] = None    # only present if a JD was provided
    contact: ContactInfo
    sections_found: List[str]
    skills_found: Dict[str, List[str]]    # grouped by category
    word_count: int
    strengths: List[str]
    improvements: List[str]
    ai_suggestions: List[str] = []        # only filled if GROQ_API_KEY is set


class UserProfile(BaseModel):
    google_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: str
    last_login_at: str
    is_new_user: bool   # True on the very first sign-in (i.e. sign up)
