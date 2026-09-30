from backend.services.resume_parser import (
    detect_sections,
    extract_contact_info,
    extract_skills,
    find_metrics,
    normalize_skill,
    parse_resume,
)

SAMPLE = """Test User
test.user@gmail.com | +91 91234 56789 | linkedin.com/in/test-user | github.com/testuser
EDUCATION
B.Tech CSE (2023 - 2027)
TECHNICAL SKILLS
Python, ReactJS, Node.js, C++, MongoDB
PROJECTS
- Built a chat app used by 200 users
- Reduced load time by 30%
- Worked on the backend
"""


def test_contact_info():
    contact = extract_contact_info(SAMPLE)
    assert contact["email"] == "test.user@gmail.com"
    assert contact["phone"] is not None
    assert "linkedin.com/in/test-user" in contact["linkedin"]
    assert "github.com/testuser" in contact["github"]


def test_year_range_is_not_a_phone_number():
    assert extract_contact_info("B.Tech 2023 - 2027")["phone"] is None


def test_sections():
    assert detect_sections(SAMPLE) == ["education", "projects", "skills"]


def test_skills_and_aliases():
    skills = [s for group in extract_skills(SAMPLE).values() for s in group]
    assert "python" in skills
    assert "react" in skills        # found through the alias "ReactJS"
    assert "c++" in skills
    assert "github" not in skills   # URL should not count as a skill


def test_no_false_positive_single_letters():
    # 'c' must not match inside words like "chat" or "code"
    skills = [s for group in extract_skills("I wrote code for a chat app").values() for s in group]
    assert "c" not in skills


def test_normalize_skill():
    assert normalize_skill(" Postgres ") == "postgresql"
    assert normalize_skill("Python") == "python"


def test_metrics_and_weak_phrases():
    assert len(find_metrics(SAMPLE)) == 2
    parsed = parse_resume(SAMPLE)
    assert "worked on" in parsed["weak_phrases"]
    assert "built" in parsed["action_verbs"]
    assert len(parsed["bullets"]) == 3
