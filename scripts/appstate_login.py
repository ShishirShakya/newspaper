"""
Optional auto-fill for App State Shibboleth login using .env credentials.

If APPSTATE_LOGIN and APPSTATE_PASSWORD are set in .env, the scripts will
fill the login form when redirected to the App State sign-in page. You may
still need to complete 2FA manually. Never commit .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


async def try_auto_fill_appstate(page) -> bool:
    """
    If the current page is the App State Shibboleth login form and .env has
    APPSTATE_LOGIN and APPSTATE_PASSWORD, fill the form and click Sign in.
    Returns True if auto-fill was attempted.
    """
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
