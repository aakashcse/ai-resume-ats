"""
Tests for Google Sign-In protection.

We can't get real tokens from Google in a test, so we create our own RSA key
pair, sign JWTs with it exactly like Google does, and tell google-auth to use
our public key instead of downloading Google's. Everything else (signature,
issuer, audience, expiry checks) runs through the real verification code.
"""

import time
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
from google.auth import crypt, jwt

from backend.main import app
from tests.conftest import TEST_CLIENT_ID

KEY_ID = "test-key-1"


def _make_key_and_cert():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    return key_pem, cert.public_bytes(serialization.Encoding.PEM)


PRIVATE_KEY, CERT = _make_key_and_cert()
OTHER_PRIVATE_KEY, _ = _make_key_and_cert()  # a key Google never published


@pytest.fixture(autouse=True)
def fake_google_certs(monkeypatch):
    """Serve our test certificate instead of downloading Google's."""
    monkeypatch.setattr("google.oauth2.id_token._fetch_certs", lambda request, url: {KEY_ID: CERT})


@pytest.fixture
def client():
    app.dependency_overrides.clear()  # use the REAL get_current_user here
    return TestClient(app)


def make_token(private_key=PRIVATE_KEY, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": TEST_CLIENT_ID,
        "sub": "google-user-42",
        "email": "aakash@gmail.com",
        "email_verified": True,
        "name": "Aakash Singh",
        "picture": "https://example.com/pic.png",
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    signer = crypt.RSASigner.from_string(private_key, key_id=KEY_ID)
    return jwt.encode(signer, claims).decode()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def upload(client, headers=None):
    with open("sample_data/sample_resume.pdf", "rb") as f:
        return client.post("/analyze", files={"resume": ("r.pdf", f, "application/pdf")}, headers=headers or {})


# ---------------------------------------------------------------- access control
def test_analyze_requires_login(client):
    response = upload(client)
    assert response.status_code == 401
    assert "sign in" in response.json()["detail"].lower()


def test_analyze_works_with_valid_google_token(client):
    response = upload(client, auth_header(make_token()))
    assert response.status_code == 200
    assert "ats_score" in response.json()


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


# ---------------------------------------------------------------- invalid tokens
@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        make_token(private_key=OTHER_PRIVATE_KEY),              # forged signature
        make_token(aud="some-other-app.apps.googleusercontent.com"),  # issued for another app
        make_token(iss="https://evil.example.com"),             # not issued by Google
        make_token(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600),  # expired
        make_token(email_verified=False),                        # unverified email
    ],
    ids=["garbage", "forged", "wrong-audience", "wrong-issuer", "expired", "unverified-email"],
)
def test_invalid_tokens_are_rejected(client, token):
    assert upload(client, auth_header(token)).status_code == 401


def test_tampered_token_is_rejected(client):
    header, payload, signature = make_token().split(".")
    tampered = ".".join([header, payload[:-2] + "AA", signature])
    assert upload(client, auth_header(tampered)).status_code == 401


def test_fails_closed_when_auth_not_configured(client, monkeypatch):
    from backend import config
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", "")
    assert upload(client, auth_header(make_token())).status_code == 503


# ---------------------------------------------------------------- sign up / sign in
def test_first_login_signs_up_then_signs_in(client):
    first = client.get("/auth/me", headers=auth_header(make_token()))
    assert first.status_code == 200
    assert first.json()["is_new_user"] is True
    assert first.json()["email"] == "aakash@gmail.com"

    second = client.get("/auth/me", headers=auth_header(make_token()))
    assert second.json()["is_new_user"] is False
    assert second.json()["created_at"] == first.json()["created_at"]


def test_me_requires_login(client):
    assert client.get("/auth/me").status_code == 401
