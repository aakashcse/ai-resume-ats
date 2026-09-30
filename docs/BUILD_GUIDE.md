# Build Guide & Interview Notes

This file explains how the project was built step by step, how it differs from the reference project, and how to talk about it in an interview.

---

## 1. Comparison with the reference project

The reference project ([ai-resume-ats](https://github.com/shradha-khapra/ai-resume-ats)) uses FastAPI + Streamlit + Groq LLM + spaCy + Sentence Transformers + Supabase + WeasyPrint.

| Area | Reference project | This project | Why |
|------|-------------------|--------------|-----|
| Resume parsing | Groq LLM returns JSON (**required**) | Regex + keyword dictionary (offline) | Needs no API key, gives the same result every run, and every decision is explainable |
| Similarity | Sentence Transformers (~80 MB model) + spaCy | TF-IDF + cosine similarity (scikit-learn) | Lightweight, fast, and easy to explain mathematically |
| Login | Supabase auth (email/password + Google) | Google Sign-In only: Streamlit OIDC + `google-auth` verification + SQLite users table | No third-party auth service to set up; the backend verifies Google's tokens directly |
| History | Supabase database | Removed | Not part of the core idea |
| PDF report export | WeasyPrint (needs system libraries) | Removed | Hard to install on Windows; not core |
| File type check | `python-magic` (needs libmagic) | Checks the file's "magic bytes" (`%PDF`, `PK`) | Same safety with no system dependency |
| Grammar / location checks | Stubs that always return "perfect" | Removed | They gave every resume free points |
| LLM | Required | Optional "AI Suggestions" | The app still works without a key |
| Tests | None | 19 pytest tests | Proves the app works |

Bugs noticed in the reference while studying it:
- `validate_file()` returns 2 values instead of 3 for an empty file, so it crashes.
- The spaCy fallback model name has a stray quote (`'"en_core_web_sm'`).
- The frontend displays `strengths`, but the API never fills that field in.
- The README mentions `.env.example`, but the file doesn't exist.

---

## 2. Step-by-step build order

Build and test the project in this order. Each step only depends on the ones before it.

**Step 1: Setup.** Create the folders, a virtual environment and `requirements.txt`.

**Step 2: `backend/config.py`.** Put every setting and scoring weight in one place.

**Step 3: `backend/data/keywords.py`.** Write the word lists: skills by category, aliases, action verbs, weak phrases and section headings.

**Step 4: `services/text_extractor.py`.**
- Validate the file: empty → too big → wrong extension → wrong magic bytes.
- Extract PDF text with pdfplumber and DOCX text with python-docx (paragraphs, tables and hyperlinks).
- Some PDFs produce `(cid:127)` instead of `•`, so it is replaced.
- Try it: `python -c "from backend.services.text_extractor import extract_text; print(extract_text(open('sample_data/sample_resume.pdf','rb').read(), 'a.pdf'))"`

**Step 5: `services/resume_parser.py`.**
- Regex for email, phone, LinkedIn and GitHub.
- Section detection: a short line that matches a known heading.
- Skill detection uses **whole-word matching** (`_contains_term`), so `"c"` doesn't match inside `"chat"`.
- Action verbs, metrics (`40%`, `500+ users`), bullets and weak phrases.

**Step 6: `services/jd_matcher.py`.** Compute skill coverage and TF-IDF similarity, then combine them into `match_score`.

**Step 7: `services/scorer.py`.** Write one function per category. Each returns `{score, max_score, details}`.

**Step 8: `services/feedback.py`.** Use simple if/else rules to turn the numbers into advice.

**Step 9: `services/analyzer.py`.** Chain steps 5–8 into one function, `analyze_resume(text, jd)`.

**Step 10: `backend/main.py`.** Create the FastAPI app and the `/analyze` endpoint. It turns a `FileError` into an HTTP 400 response.
- Test it at http://localhost:8000/docs.

**Step 11: `frontend/app.py`.** Build the Streamlit UI. It sends the file to the API and displays the JSON response.

**Step 11b: Google Sign-In.**
- `backend/auth.py`: the `get_current_user` dependency verifies the `Authorization: Bearer` token with `google.oauth2.id_token.verify_oauth2_token`.
- `backend/users.py`: `get_or_create_user()` stores a user on their first sign-in (sign up).
- `backend/main.py`: add `user = Depends(get_current_user)` to `/analyze`, and add `GET /auth/me`.
- `frontend/auth_ui.py`: the sign-in page (`st.login("google")`), the account sidebar (`st.logout()`) and session-expired handling.
- `frontend/app.py`: the gate at the top of `main()`. It sends `st.user.tokens["id"]` with every request.
- `tests/test_auth.py`: signs test JWTs with our own RSA key and checks that forged, expired, wrong-audience and wrong-issuer tokens are rejected.

**Step 12: Tests and README.** Write the tests and README, then run `pytest`.

---

## 3. Interview talking points

**30-second pitch:**
> "I built a Resume ATS Scorer with a FastAPI backend and a Streamlit frontend. It extracts text from PDF or DOCX resumes and detects sections, skills, action verbs and quantified achievements using regex and a skill dictionary. It then gives a transparent score out of 100. If you paste a job description, it computes skill coverage and TF-IDF cosine similarity to show how well you match, and it lists the missing skills. I kept it offline and explainable, and I covered it with pytest tests."

**Likely questions:**

- **What is TF-IDF?**
  Term Frequency × Inverse Document Frequency. A word gets a high weight when it appears often in one document but is rare across documents. Common words like "the" get low weight.

- **What is cosine similarity?**
  `cos θ = (A·B) / (|A| |B|)`. It measures the angle between two vectors and ignores their length, so a long resume isn't penalised just for being long. 1 means very similar and 0 means unrelated.

- **Why multiply the similarity by 2?**
  A resume and a JD are very different kinds of documents, so raw TF-IDF similarity rarely goes above ~0.5 even for good matches. Scaling it makes the 0–100 number easier to read. It is capped at 1.

- **Why not use an LLM for everything?**
  LLMs cost money, need a key, are slower, and can give different answers for the same resume. Rule-based scoring is deterministic and explainable. I added the LLM only as an optional extra.

- **Why separate the backend and frontend?**
  Separation of concerns. The API could serve a React app or a mobile app later, and it can be tested on its own.

- **How do you validate uploads?**
  I check the size, extension and magic bytes (`%PDF` / `PK`). I also check the amount of extracted text, which catches scanned image-only PDFs.

- **How does your login work? / What is OAuth / OpenID Connect?**
  OAuth 2.0 lets a user grant an app access without sharing their password. OpenID Connect (OIDC) is a layer on top of it that adds identity: Google returns an **ID token**, a JWT saying who the user is. The frontend redirects to Google, Google redirects back with a one-time code, and Streamlit exchanges the code for the ID token.

- **What is a JWT and how do you verify it?**
  A JWT has three parts, `header.payload.signature`. Google signs it with its private RSA key (RS256). The backend verifies it with Google's public keys, and then checks the issuer, the audience (my Client ID), the expiry and `email_verified`. If anyone edits the payload, the signature no longer matches.

- **Why verify in the backend if the frontend already has a login?**
  Anyone can call an API directly with curl or Postman. The frontend gate is for user experience; the backend check is the real security.

- **Why check the audience?**
  A token that Google issued for *another* app is still validly signed by Google. Checking `aud` makes sure the token was issued for my app.

- **What are `state` and `nonce`?**
  Random values that protect the login redirect. `state` protects against CSRF, and `nonce` protects against replayed tokens. Streamlit handles both.

- **Why store users at all?**
  So that the first sign-in counts as a real "sign up" (created_at, last_login_at). It is also the foundation for features like saving past analyses.

- **Limitations and next steps?**
  The skill list is dictionary-based, so it misses skills that aren't listed. Next steps could be semantic skill matching with sentence embeddings, section-level scoring, or a React frontend.
