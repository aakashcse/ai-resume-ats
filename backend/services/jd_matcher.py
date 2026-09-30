"""
Step 3 (optional): compare the resume with a job description.

Two simple signals are combined:
1. Keyword coverage  - what % of the skills the JD asks for appear in the resume.
2. Text similarity   - TF-IDF + cosine similarity between the two full texts.
"""

from typing import Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import KEYWORD_WEIGHT, SIMILARITY_WEIGHT
from backend.services.resume_parser import extract_skills, flatten_skills


def text_similarity(resume_text: str, jd_text: str) -> float:
    """Return a 0-1 similarity score between two texts.

    TF-IDF turns each text into a vector where important, less common words
    get higher weights. Cosine similarity then measures the angle between
    the two vectors: 1.0 = same direction (very similar), 0.0 = unrelated.
    """
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vectors = vectorizer.fit_transform([resume_text, jd_text])
    return float(cosine_similarity(vectors[0], vectors[1])[0][0])


def match_resume_to_jd(resume_text: str, jd_text: str) -> Dict:
    resume_skills = set(flatten_skills(extract_skills(resume_text)))
    jd_skills = flatten_skills(extract_skills(jd_text))

    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]

    coverage = len(matched) / len(jd_skills) if jd_skills else 0.0

    # Raw TF-IDF similarity between a resume and a JD rarely goes above ~0.5
    # even for a great match, so we scale it up (and cap at 1.0) to make the
    # number more meaningful on a 0-100 scale.
    similarity = min(text_similarity(resume_text, jd_text) * 2, 1.0)

    if jd_skills:
        match_score = (coverage * KEYWORD_WEIGHT + similarity * SIMILARITY_WEIGHT) * 100
    else:
        # The JD mentions no skills we know about -> rely on text similarity only.
        match_score = similarity * 100

    return {
        "match_score": round(match_score, 1),
        "keyword_coverage": round(coverage * 100, 1),
        "text_similarity": round(similarity * 100, 1),
        "matched_skills": matched,
        "missing_skills": missing,
    }
