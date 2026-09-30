"""
Step 5: turn the scores into human-readable strengths and improvements.
"""

from typing import Dict, List, Optional, Tuple

from backend.config import IDEAL_MAX_WORDS, IDEAL_MIN_WORDS

SECTION_TIPS = {
    "education": "Add an 'Education' section with your degree, college and graduation year.",
    "skills": "Add a 'Skills' section listing your technical skills — ATS systems scan it first.",
    "projects": "Add a 'Projects' section with 2–3 projects, the tech stack used and a GitHub link.",
    "experience": "Add an 'Experience' or 'Internships' section (internships, freelance or open-source count).",
    "summary": "Add a 2–3 line 'Summary' at the top describing your role, key skills and goal.",
    "certifications": "Add 'Certifications' or 'Achievements' (courses, hackathons, coding ranks).",
}


def generate_feedback(parsed: Dict, scores: Dict, jd_result: Optional[Dict] = None) -> Tuple[List[str], List[str]]:
    strengths: List[str] = []
    improvements: List[str] = []

    # --- Sections ---
    for section, tip in SECTION_TIPS.items():
        if section not in parsed["sections"]:
            improvements.append(tip)
    if len(parsed["sections"]) >= 5:
        strengths.append("Well-structured resume with all the standard sections.")

    # --- Contact ---
    contact = parsed["contact"]
    if not contact["email"]:
        improvements.append("Add a professional email address — recruiters can't contact you without it.")
    if not contact["phone"]:
        improvements.append("Add a phone number with country code.")
    if not contact["linkedin"]:
        improvements.append("Add your LinkedIn profile URL.")
    if not contact["github"]:
        improvements.append("Add your GitHub profile URL so recruiters can see your code.")
    if all(contact.values()):
        strengths.append("Complete contact details, including LinkedIn and GitHub.")

    # --- Skills ---
    skill_count = len(parsed["skills"])
    if skill_count >= 12:
        strengths.append(f"Strong technical skill set ({skill_count} skills detected).")
    elif skill_count < 6:
        improvements.append("List more relevant technical skills (languages, frameworks, tools, databases).")

    # --- Content ---
    if len(parsed["action_verbs"]) >= 8:
        strengths.append("Good use of strong action verbs (e.g. " + ", ".join(parsed["action_verbs"][:4]) + ").")
    else:
        improvements.append("Start bullet points with strong action verbs like Developed, Built, Optimized, Led.")

    if len(parsed["metrics"]) >= 4:
        strengths.append("Achievements are quantified with numbers — great for showing impact.")
    else:
        improvements.append("Quantify your impact with numbers, e.g. 'Reduced load time by 40%' or 'Used by 500+ students'.")

    if len(parsed["bullets"]) < 6:
        improvements.append("Use bullet points for experience and projects — they are easier for ATS and recruiters to scan.")

    if parsed["weak_phrases"]:
        improvements.append(
            "Replace weak phrases (" + ", ".join(f"'{p}'" for p in parsed["weak_phrases"])
            + ") with action verbs describing what YOU did."
        )

    # --- Length ---
    words = parsed["word_count"]
    if words < IDEAL_MIN_WORDS:
        improvements.append(f"Your resume is short ({words} words). Add more detail to projects and experience.")
    elif words > IDEAL_MAX_WORDS:
        improvements.append(f"Your resume is long ({words} words). Keep it to 1 page as a fresher.")

    # --- Job description ---
    if jd_result:
        if jd_result["missing_skills"]:
            top_missing = ", ".join(jd_result["missing_skills"][:8])
            improvements.insert(0, f"Add these job-description skills if you genuinely have them: {top_missing}.")
        if jd_result["match_score"] >= 70:
            strengths.insert(0, "Strong match with the job description.")

    if not strengths:
        strengths.append("Your resume has a readable text layer, so ATS systems can parse it.")

    return strengths, improvements
