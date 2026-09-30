"""
OPTIONAL: extra resume tips from an LLM (Groq, Llama 3).

The app works fully without this. It only runs when GROQ_API_KEY is set in
the .env file, and any error here is ignored so it can never break scoring.
"""

import logging
from typing import List, Optional

from backend.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

PROMPT = """You are an expert technical recruiter. Read the resume below{jd_part}
and give exactly 5 short, specific, actionable suggestions to improve it.
Return one suggestion per line with no numbering and no extra text.

RESUME:
{resume}
{jd_block}"""


def get_ai_suggestions(resume_text: str, jd_text: Optional[str] = None) -> List[str]:
    if not GROQ_API_KEY:
        return []

    try:
        from groq import Groq  # imported here so the package is only needed if you use it

        prompt = PROMPT.format(
            jd_part=" and the job description" if jd_text else "",
            resume=resume_text[:6000],
            jd_block=f"\nJOB DESCRIPTION:\n{jd_text[:3000]}" if jd_text else "",
        )
        response = Groq(api_key=GROQ_API_KEY).chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        content = response.choices[0].message.content or ""
        lines = [line.strip("-•* ").strip() for line in content.splitlines()]
        return [line for line in lines if line][:5]
    except Exception as exc:
        logger.warning("AI suggestions skipped: %s", exc)
        return []
