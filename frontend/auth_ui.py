"""
Sign-in page and account helpers for the Streamlit frontend.

Streamlit has built-in OpenID Connect (OIDC) login:
  - st.login("google")  sends the user to Google's sign-in page
  - st.user             holds the signed-in user's info (name, email, picture)
  - st.logout()         clears the session cookie

Streamlit handles the OAuth details for us (redirect, `state` + `nonce`
checks against CSRF/replay attacks, exchanging the code for tokens) and
stores the identity in a signed, HTTP-only cookie.
Configuration lives in .streamlit/secrets.toml (see secrets.toml.example).
"""

import requests
import streamlit as st

PROVIDER = "google"

# Google "G" logo as a small inline SVG, shown on the sign-in button.
GOOGLE_LOGO = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
    "<path fill='%23EA4335' d='M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z'/>"
    "<path fill='%234285F4' d='M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z'/>"
    "<path fill='%23FBBC05' d='M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z'/>"
    "<path fill='%2334A853' d='M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z'/>"
    "</svg>"
)

LOGIN_CSS = f"""
<style>
.st-key-google_login button {{
    background: #ffffff url("{GOOGLE_LOGO}") no-repeat 16px center;
    background-size: 20px 20px;
    color: #1f1f1f;
    border: 1px solid #747775;
    border-radius: 999px;
    padding: 0.6rem 1rem 0.6rem 2.8rem;
    font-weight: 500;
}}
.st-key-google_login button:hover {{ background-color: #f2f2f2; border-color: #1f1f1f; color: #1f1f1f; }}
</style>
"""


def auth_is_configured() -> bool:
    """True if .streamlit/secrets.toml has an [auth] section for Google."""
    try:
        return PROVIDER in st.secrets.get("auth", {})
    except FileNotFoundError:
        return False


def is_logged_in() -> bool:
    return bool(st.user.get("is_logged_in"))


def get_id_token() -> str:
    """The Google ID token, sent to the backend as proof of who the user is.
    Never display or log this value."""
    return st.user.tokens.get("id", "")


def show_setup_error() -> None:
    st.error(
        "**Google Sign-In is not configured.** "
        "Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your "
        "Google OAuth credentials. See the *Authentication setup* section in the README."
    )


def show_login_page() -> None:
    """Shown to everyone who is not signed in. The scorer stays hidden."""
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.6, 1])
    with center:
        st.markdown(
            "<h1 style='text-align:center;margin-bottom:0;'>📄 Resume ATS Scorer</h1>"
            "<p style='text-align:center;opacity:0.75;margin-top:0.4rem;'>"
            "See how Applicant Tracking Systems read your resume and how well you match a job."
            "</p>",
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("#### Sign in to continue")
            st.markdown(
                "- Overall ATS score with a clear breakdown\n"
                "- Matched and missing skills for any job description\n"
                "- Specific tips to improve your resume"
            )
            if st.button("Continue with Google", key="google_login", use_container_width=True):
                st.login(PROVIDER)
            st.caption(
                "New here? Continuing with Google creates your account automatically. "
                "We only receive your name, email and profile picture — never your password."
            )


def register_user_with_backend(backend_url: str) -> None:
    """Register/load the user once per session. The first sign-in creates the
    account (sign up). In API mode this calls GET /auth/me, where the backend
    verifies the token; in standalone mode it writes to the user store directly."""
    if "profile" in st.session_state:
        return

    if not backend_url:
        profile = _register_in_process()
    else:
        profile = _register_via_api(backend_url)

    st.session_state["profile"] = profile
    first_name = (profile.get("name") or "there").split()[0]
    if profile["is_new_user"]:
        st.toast(f"Welcome, {first_name}! Your account has been created.", icon="🎉")
    else:
        st.toast(f"Welcome back, {first_name}!", icon="👋")


def _register_in_process() -> dict:
    """Standalone mode: Streamlit has already verified Google's ID token during
    st.login(), so we can trust st.user and write to the user store directly."""
    if not st.user.get("email_verified", False):
        st.error("Your Google account email is not verified. Please use a verified Google account.")
        st.stop()

    from backend.users import get_or_create_user

    user, is_new = get_or_create_user(
        google_id=st.user["sub"],
        email=st.user["email"],
        name=st.user.get("name", ""),
        picture=st.user.get("picture", ""),
    )
    return {**user, "is_new_user": is_new}


def _register_via_api(backend_url: str) -> dict:
    response = requests.get(
        f"{backend_url}/auth/me",
        headers={"Authorization": f"Bearer {get_id_token()}"},
        timeout=15,
    )
    if response.status_code == 401:
        st.session_state["session_expired"] = True
        st.rerun()
    response.raise_for_status()
    return response.json()


def show_account_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Account")
        if st.user.get("picture"):
            st.image(st.user["picture"], width=64)
        st.markdown(f"**{st.user.get('name', '')}**")
        st.caption(st.user.get("email", ""))
        if st.button("Sign out", icon=":material/logout:", use_container_width=True):
            st.session_state.clear()
            st.logout()


def show_session_expired() -> None:
    st.warning("Your sign-in session has expired. Please sign in again to continue.")
    if st.button("Sign in again", type="primary"):
        st.session_state.clear()
        st.logout()
