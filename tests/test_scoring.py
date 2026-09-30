from backend.services.analyzer import analyze_resume
from backend.services.jd_matcher import match_resume_to_jd

GOOD = """Test User
test@example.com | +91 91234 56789 | linkedin.com/in/test | github.com/test
SUMMARY
Developer skilled in Python, React and FastAPI.
EDUCATION
B.Tech CSE
SKILLS
Python, React, FastAPI, Docker, MongoDB, Git, AWS, SQL
EXPERIENCE
- Developed APIs serving 1,000 users
- Optimized queries, improving speed by 35%
PROJECTS
- Built a React dashboard used by 50 students
- Deployed services with Docker on AWS
CERTIFICATIONS
AWS Cloud Practitioner
"""

WEAK = "Test User\nI am a hard working person. Worked on some things. Responsible for tasks."


def test_score_ranges():
    result = analyze_resume(GOOD)
    assert 0 <= result["ats_score"] <= 100
    for category in result["breakdown"].values():
        assert 0 <= category["score"] <= category["max_score"]
    total_max = sum(c["max_score"] for c in result["breakdown"].values())
    assert total_max == 100


def test_good_resume_beats_weak_resume():
    assert analyze_resume(GOOD)["ats_score"] > analyze_resume(WEAK)["ats_score"] + 30


def test_no_jd_means_no_jd_match():
    result = analyze_resume(GOOD, "")
    assert result["jd_match"] is None
    assert result["ats_score"] == result["resume_quality_score"]


def test_jd_matching():
    jd = "We need a Python developer with FastAPI, Docker, Kubernetes and PostgreSQL."
    match = match_resume_to_jd(GOOD, jd)
    assert "python" in match["matched_skills"]
    assert "kubernetes" in match["missing_skills"]
    assert 0 <= match["match_score"] <= 100


def test_relevant_jd_scores_higher_than_unrelated_jd():
    relevant = match_resume_to_jd(GOOD, "Python React FastAPI Docker AWS developer")
    unrelated = match_resume_to_jd(GOOD, "Chartered accountant for tax auditing and bookkeeping")
    assert relevant["match_score"] > unrelated["match_score"]


def test_feedback_mentions_missing_jd_skills():
    result = analyze_resume(GOOD, "Looking for Kubernetes and Terraform experience")
    assert "kubernetes" in result["improvements"][0]
