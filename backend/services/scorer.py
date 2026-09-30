"""
Step 4: turn the parsed resume into scores.

Resume quality is scored out of 100 using four categories (see
SCORE_WEIGHTS in config.py). Every category returns its points plus a list
of short "details" so the user can see exactly why they got that score.
"""

import re
from typing import Dict, Optional

from backend.config import (
    IDEAL_MAX_WORDS,
    IDEAL_MIN_WORDS,
    JD_MATCH_WEIGHT,
    QUALITY_WEIGHT,
    SCORE_WEIGHTS,
)

# Points for each section (adds up to SCORE_WEIGHTS["sections"] = 25).
SECTION_POINTS = {
    "education": 5,
    "skills": 5,
    "projects": 5,
    "experience": 5,
    "summary": 3,
    "certifications": 2,
}


def _category(score: float, max_score: float, details: list) -> Dict:
    return {"score": round(min(score, max_score), 1), "max_score": max_score, "details": details}


def score_sections(parsed: Dict) -> Dict:
    found = parsed["sections"]
    score = sum(points for section, points in SECTION_POINTS.items() if section in found)
    missing = [s for s in SECTION_POINTS if s not in found]
    details = [f"Found: {', '.join(found) or 'none'}"]
    if missing:
        details.append(f"Missing: {', '.join(missing)}")
    return _category(score, SCORE_WEIGHTS["sections"], details)


def score_skills(parsed: Dict) -> Dict:
    count = len(parsed["skills"])
    categories = len(parsed["skills_grouped"])
    # 1 point per skill (max 15) + 1 point per skill category covered (max 5).
    score = min(count, 15) + min(categories, 5)
    details = [f"{count} recognised skills across {categories} categories"]
    return _category(score, SCORE_WEIGHTS["skills"], details)


def score_content(parsed: Dict) -> Dict:
    verbs = len(parsed["action_verbs"])
    metrics = len(parsed["metrics"])
    bullets = len(parsed["bullets"])
    weak = len(parsed["weak_phrases"])

    verb_points = min(verbs * 1.5, 12)      # up to 12 pts: strong action verbs
    metric_points = min(metrics * 2, 12)    # up to 12 pts: numbers that show impact
    bullet_points = min(bullets, 11)        # up to 11 pts: bullet-point structure
    penalty = min(weak * 2, 6)              # lose up to 6 pts for weak phrases

    score = max(verb_points + metric_points + bullet_points - penalty, 0)
    details = [
        f"{verbs} distinct action verbs",
        f"{metrics} quantified achievements (numbers, %, users...)",
        f"{bullets} bullet points",
    ]
    if weak:
        details.append(f"-{penalty} for weak phrases: {', '.join(parsed['weak_phrases'])}")
    return _category(score, SCORE_WEIGHTS["content"], details)


def score_formatting(parsed: Dict) -> Dict:
    contact = parsed["contact"]
    words = parsed["word_count"]
    score = 0
    details = []

    # Contact info: 10 points
    for field, points in (("email", 4), ("phone", 3), ("linkedin", 1.5), ("github", 1.5)):
        if contact.get(field):
            score += points
    found = [f for f in ("email", "phone", "linkedin", "github") if contact.get(f)]
    details.append(f"Contact info: {', '.join(found) or 'none found'}")

    # Length: 6 points
    if IDEAL_MIN_WORDS <= words <= IDEAL_MAX_WORDS:
        score += 6
        details.append(f"Good length ({words} words)")
    elif words < IDEAL_MIN_WORDS:
        score += 6 * words / IDEAL_MIN_WORDS
        details.append(f"A bit short ({words} words; aim for {IDEAL_MIN_WORDS}-{IDEAL_MAX_WORDS})")
    else:
        score += 3
        details.append(f"Quite long ({words} words; aim for under {IDEAL_MAX_WORDS})")

    # ATS-unfriendly characters (table borders, icons, emoji): 4 points
    odd_chars = len(re.findall(r"[│┤├┼┴┬╔╗╚╝═║-\U0001F300-\U0001FAFF]", parsed["text"]))
    if odd_chars == 0:
        score += 4
        details.append("No ATS-unfriendly symbols detected")
    else:
        score += max(4 - odd_chars / 5, 0)
        details.append(f"{odd_chars} special symbols/icons that ATS may not read")

    return _category(score, SCORE_WEIGHTS["formatting"], details)


def get_rating(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Average"
    return "Needs Improvement"


def calculate_scores(parsed: Dict, jd_result: Optional[Dict] = None) -> Dict:
    breakdown = {
        "sections": score_sections(parsed),
        "skills": score_skills(parsed),
        "content": score_content(parsed),
        "formatting": score_formatting(parsed),
    }
    quality = sum(c["score"] for c in breakdown.values())  # already out of 100

    if jd_result:
        final = quality * QUALITY_WEIGHT + jd_result["match_score"] * JD_MATCH_WEIGHT
    else:
        final = quality

    final = round(final, 1)
    return {
        "ats_score": final,
        "rating": get_rating(final),
        "resume_quality_score": round(quality, 1),
        "breakdown": breakdown,
    }
