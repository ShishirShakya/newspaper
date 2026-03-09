"""
Optional auto-fill for App State Shibboleth login using .env credentials.

Set AUTOMATIC=TRUE in .env to auto-fill the login form with APPSTATE_LOGIN and
APPSTATE_PASSWORD when the script opens the App State sign-in page. Set
AUTOMATIC=FALSE to type your credentials manually in the browser. Never commit .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _is_automatic_enabled() -> bool:
    """Return True if .env has AUTOMATIC set to a truthy value (TRUE, 1, YES)."""
    val = os.getenv("AUTOMATIC", "").strip().upper()
    return val in ("TRUE", "1", "YES")


async def try_auto_fill_appstate(page) -> bool:
    """
    If AUTOMATIC is TRUE in .env and the current page is the App State Shibboleth
    login form, fill the form with APPSTATE_LOGIN and APPSTATE_PASSWORD and click
    Sign in. If AUTOMATIC is FALSE, do nothing (user types credentials manually).
    Returns True if auto-fill was attempted.
    """
    if not _is_automatic_enabled():
        return False
    if "appstate" not in page.url.lower():
        return False
    login = os.getenv("APPSTATE_LOGIN", "").strip()
    password = os.getenv("APPSTATE_PASSWORD", "").strip()
    if not login or not password:
        return False
    try:
        # App State Shibboleth: "login or email" and "password" (label or placeholder)
        login_input = page.get_by_label("login or email").or_(page.get_by_placeholder("login or email")).first
        await login_input.wait_for(state="visible", timeout=5000)
        await login_input.fill(login)
        password_input = page.get_by_label("password").or_(page.get_by_placeholder("password")).first
        await password_input.fill(password)
        await page.get_by_role("button", name="Sign in").click()
        return True
    except Exception:
        return False
