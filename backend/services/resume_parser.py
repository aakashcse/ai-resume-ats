"""
Step 2 of the pipeline: pull structured information out of the resume text.

Everything here is rule-based (regular expressions + keyword lists), so it
works offline and every result can be traced back to a simple rule.
"""

import re
from typing import Dict, List

from backend.data.keywords import (
    ACTION_VERBS,
    SECTION_HEADINGS,
    SKILL_ALIASES,
    SKILLS,
    WEAK_PHRASES,
)

# ---------- Regular expressions ----------
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,5}")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", re.I)
BULLET_RE = re.compile(r"^\s*(?:[•●▪■◦\-\*–]|\d+[.)])\s+")

# Numbers that show impact: 40%, 10k, 500+ users, $2M, 3x, ...
METRIC_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s*(?:%|\+|x\b|k\b|m\b|lpa\b)"
    r"|\$\s?\d+"
    r"|\b\d[\d,]*\s+(?:users|customers|clients|students|projects|requests|records|hours|days|members|downloads)",
    re.I,
)


def normalize_skill(skill: str) -> str:
    """Map different spellings to one name, e.g. 'ReactJS' -> 'react'."""
    cleaned = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def _contains_term(term: str, text_lower: str) -> bool:
    """Whole-word search that also works for terms like 'c++', 'node.js' or 'ci/cd'.
    Plain `term in text` would wrongly find 'r' inside 'react', 'go' inside 'google', etc."""
    pattern = r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#])"
    return re.search(pattern, text_lower) is not None


def extract_contact_info(text: str) -> Dict[str, str]:
    email = EMAIL_RE.search(text)
    linkedin = LINKEDIN_RE.search(text)
    github = GITHUB_RE.search(text)

    phone = None
    for match in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 10 <= len(digits) <= 13:  # ignore years like "2023 - 2027"
            phone = match.group().strip()
            break

    return {
        "email": email.group() if email else None,
        "phone": phone,
        "linkedin": linkedin.group() if linkedin else None,
        "github": github.group() if github else None,
    }


def detect_sections(text: str) -> List[str]:
    """Find standard section headings. A heading is a short line that
    matches a known section name (e.g. 'EDUCATION', 'Technical Skills:')."""
    found = set()
    for line in text.splitlines():
        cleaned = re.sub(r"[^a-z& ]", "", line.lower()).strip()
        if not cleaned or len(cleaned.split()) > 4:
            continue
        for section, headings in SECTION_HEADINGS.items():
            if cleaned in headings:
                found.add(section)
    # Keep a fixed order so the output is predictable.
    return [s for s in SECTION_HEADINGS if s in found]


def extract_skills(text: str) -> Dict[str, List[str]]:
    """Return known skills found in the text, grouped by category."""
    # Remove URLs and emails first so "github.com/you" doesn't count as the skill "github".
    text_lower = re.sub(r"\S+@\S+|(?:https?://)?(?:www\.)?\S+\.(?:com|in|io|dev|app)\S*", " ", text.lower())

    # Also count aliases, e.g. "ReactJS" in the resume counts as "react".
    alias_hits = {canonical for alias, canonical in SKILL_ALIASES.items()
                  if _contains_term(alias, text_lower)}

    found: Dict[str, List[str]] = {}
    for category, skills in SKILLS.items():
        matches = [s for s in skills if s in alias_hits or _contains_term(s, text_lower)]
        if matches:
            found[category] = matches
    return found


def flatten_skills(grouped: Dict[str, List[str]]) -> List[str]:
    return [skill for skills in grouped.values() for skill in skills]


def extract_bullets(text: str) -> List[str]:
    return [BULLET_RE.sub("", line).strip() for line in text.splitlines() if BULLET_RE.match(line)]


def find_action_verbs(text: str) -> List[str]:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return sorted(words & ACTION_VERBS)


def find_metrics(text: str) -> List[str]:
    return [m.group().strip() for m in METRIC_RE.finditer(text)]


def find_weak_phrases(text: str) -> List[str]:
    text_lower = text.lower()
    return [p for p in WEAK_PHRASES if p in text_lower]


def parse_resume(text: str) -> Dict:
    """Run every extractor and return one dictionary with the results."""
    skills_grouped = extract_skills(text)
    return {
        "text": text,
        "word_count": len(text.split()),
        "contact": extract_contact_info(text),
        "sections": detect_sections(text),
        "skills_grouped": skills_grouped,
        "skills": flatten_skills(skills_grouped),
        "bullets": extract_bullets(text),
        "action_verbs": find_action_verbs(text),
        "metrics": find_metrics(text),
        "weak_phrases": find_weak_phrases(text),
    }
