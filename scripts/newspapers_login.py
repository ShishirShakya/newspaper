"""
Shared login check and login flow for Newspapers.com scripts.
After the user logs in and presses Enter, navigate back to the homepage and re-check;
if not required, return True so the script can continue in the same run.
"""

import asyncio

from browser_context import wait_for_enter_or_timeout
from newspapers_config import (
    GOTO_TIMEOUT_MS,
    HOMEPAGE_URL,
    LOGIN_URL_NCLIVE_NEWSPAPERS,
    LOGIN_WAIT_SECONDS,
)


async def check_login_required(page) -> bool:
    """True only when we are clearly blocked: Unauthorized Access or on a login/signin URL."""
    url = page.url.lower()
    if "signin" in url or "shibb" in url or "unauthorized" in url or "/login" in url:
        return True
    try:
        if await page.get_by_text("Unauthorized Access").first.is_visible():
            return True
    except Exception:
        pass  # Unauthorized check best-effort; continue
    return False


async def run_login_flow_and_continue(page) -> bool:
    """
    Run the NCLIVE login flow (goto, optional auto-fill, wait for Enter), then navigate
    to the Newspapers.com homepage and re-check login. Return True if the caller can
    proceed (navigate to results, etc.); False if still not logged in or on error.
    """
    await page.goto(LOGIN_URL_NCLIVE_NEWSPAPERS, wait_until="load", timeout=GOTO_TIMEOUT_MS)
    await asyncio.sleep(3)
    from appstate_login import try_auto_fill_appstate
    if await try_auto_fill_appstate(page):
        print("Filled login from .env; complete 2FA if prompted.")
    await wait_for_enter_or_timeout(LOGIN_WAIT_SECONDS)

    try:
        await page.goto(HOMEPAGE_URL, wait_until="load", timeout=GOTO_TIMEOUT_MS)
        try:
            await page.wait_for_load_state("networkidle")
        except Exception:
            pass  # networkidle best-effort; continue without
        await asyncio.sleep(2)

        if await check_login_required(page):
            print("Still not logged in. Run again or check your session.")
            return False
        return True
    except Exception:
        print("Could not return to the homepage after login.")
        return False
