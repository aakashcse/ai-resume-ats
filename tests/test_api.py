from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.main import app

SAMPLES = Path(__file__).resolve().parent.parent / "sample_data"
TEST_USER = {"google_id": "123", "email": "test@gmail.com", "name": "Test User", "picture": ""}

# These tests are about the scoring API, so we pretend a user is already signed in.
# Real token verification is tested separately in test_auth.py.
client = TestClient(app)


@pytest.fixture(autouse=True)
def signed_in_user():
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield
    app.dependency_overrides.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_pdf_with_jd():
    jd = (SAMPLES / "sample_job_description.txt").read_text()
    with open(SAMPLES / "sample_resume.pdf", "rb") as f:
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", f, "application/pdf")},
            data={"job_description": jd},
        )
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["ats_score"] <= 100
    assert body["jd_match"] is not None
    assert body["contact"]["email"] == "riya.sharma@example.com"


def test_analyze_docx_without_jd():
    with open(SAMPLES / "sample_resume.docx", "rb") as f:
        response = client.post("/analyze", files={"resume": ("resume.docx", f)})
    assert response.status_code == 200
    assert response.json()["jd_match"] is None


def test_rejects_wrong_file_type():
    response = client.post("/analyze", files={"resume": ("resume.txt", b"hello world", "text/plain")})
    assert response.status_code == 400


def test_rejects_fake_pdf():
    response = client.post("/analyze", files={"resume": ("resume.pdf", b"not really a pdf", "application/pdf")})
    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]


def test_rejects_empty_file():
    response = client.post("/analyze", files={"resume": ("resume.pdf", b"", "application/pdf")})
    assert response.status_code == 400
