"""
Protects the API: every request must carry a valid Google ID token.

How it works
------------
1. The user clicks "Continue with Google" in the frontend and signs in on
   Google's own page (we never see their password).
2. Google gives the frontend an **ID token**: a JSON Web Token (JWT) that is
   digitally signed by Google and says who the user is.
3. The frontend sends it to this API in the header:
       Authorization: Bearer <id_token>
4. `get_current_user` verifies the token with Google's official library:
     - the signature matches Google's public keys (it wasn't forged or edited)
     - the issuer is accounts.google.com
     - the audience ("aud") is OUR client ID (it wasn't issued for another app)
     - it hasn't expired (Google ID tokens last about 1 hour)
     - the email address is verified by Google
   Any failure returns 401 Unauthorized.

Because the check happens in the backend, nobody can skip the login by
calling the API directly with curl or Postman.
"""

import logging
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from backend import config

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

# Reusing one Request object lets google-auth reuse the HTTP connection.
_google_request = google_requests.Request()


def verify_google_token(token: str) -> Dict:
    """Verify a Google ID token and return its claims. Raises ValueError if invalid."""
    claims = id_token.verify_oauth2_token(
        token,
        _google_request,
        audience=config.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10,  # tolerate small clock differences between servers
    )
    if not claims.get("email_verified"):
        raise ValueError("Google account email is not verified.")
    return claims


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict:
    """FastAPI dependency: add `user = Depends(get_current_user)` to protect a route."""
    if not config.GOOGLE_CLIENT_ID:
        # Fail closed: if auth isn't configured, refuse instead of letting everyone in.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on the server (GOOGLE_CLIENT_ID is missing).",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Please sign in with Google to use this feature.")

    try:
        claims = verify_google_token(credentials.credentials)
    except TransportError:
        # We couldn't download Google's public keys (network problem on our side).
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach Google to verify your sign-in. Please try again shortly.",
        )
    except (ValueError, GoogleAuthError) as exc:
        # Don't reveal *why* verification failed to the user; log it for us.
        logger.info("Rejected sign-in token: %s", exc)
        raise _unauthorized("Your session is invalid or has expired. Please sign in again.")
    except Exception:
        # Fail closed: if anything unexpected goes wrong while checking a
        # token, treat it as NOT signed in rather than crashing or letting it through.
        logger.exception("Unexpected error while verifying a sign-in token")
        raise _unauthorized("Your session is invalid or has expired. Please sign in again.")

    return {
        "google_id": claims["sub"],
        "email": claims["email"],
        "name": claims.get("name", ""),
        "picture": claims.get("picture", ""),
    }
