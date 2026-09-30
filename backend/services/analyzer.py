"""
The full analysis pipeline in one place:

    resume text ──► parse ──► (optional) match with JD ──► score ──► feedback

Keeping this separate from the API route means the same function can be
used from tests, a script, or a different frontend.
"""

from typing import Dict, Optional

from backend.services.ai_suggestions import get_ai_suggestions
from backend.services.feedback import generate_feedback
from backend.services.jd_matcher import match_resume_to_jd
from backend.services.resume_parser import parse_resume
from backend.services.scorer import calculate_scores


def analyze_resume(resume_text: str, jd_text: Optional[str] = None) -> Dict:
    jd_text = (jd_text or "").strip() or None

    parsed = parse_resume(resume_text)
    jd_result = match_resume_to_jd(resume_text, jd_text) if jd_text else None
    scores = calculate_scores(parsed, jd_result)
    strengths, improvements = generate_feedback(parsed, scores, jd_result)

    return {
        **scores,
        "jd_match": jd_result,
        "contact": parsed["contact"],
        "sections_found": parsed["sections"],
        "skills_found": parsed["skills_grouped"],
        "word_count": parsed["word_count"],
        "strengths": strengths,
        "improvements": improvements,
        "ai_suggestions": get_ai_suggestions(resume_text, jd_text),
    }
