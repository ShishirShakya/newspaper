"""
Newspapers.com search results screenshot (from newspapers-prompt.md).

Run from project root:
  uv sync
  uv run playwright install chromium
  uv run python scripts/newspaper_screenshot.py

Or in Cursor: use the prompt in newspapers-prompt.md so the agent uses the
browser (Playwright MCP) to do the same steps.

1. Opens the Certificate of Need (NC, 1960-2026) results URL directly
2. Waits for the page to load
3. Takes a full-page screenshot into newspapers_screenshots/
4. Prints the saved path (or prompts to log in and run again if login wall)
"""

import asyncio

from playwright.async_api import async_playwright

from browser_context import create_persistent_context, wait_for_enter_or_timeout
from newspapers_config import (
    LOGIN_URL_NCLIVE_NEWSPAPERS,
    LOGIN_WAIT_SECONDS,
    OUTPUT_DIR,
    SEARCH_URL,
    USER_DATA_DIR,
)

FILENAME = "certificate_of_need_nc_search_1960_2026.png"


async def main() -> None:
    out_path = OUTPUT_DIR / FILENAME
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await create_persistent_context(p, str(USER_DATA_DIR))
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            await asyncio.sleep(2)
            await page.goto(SEARCH_URL, wait_until="load", timeout=30_000)
            try:
                await page.wait_for_load_state("networkidle")
            except Exception:
                pass
            await asyncio.sleep(2)

            if "newspapers.com" in page.url and "/search/results/" not in page.url:
                from newspapers_search_form import fill_and_submit_search_form
                if await fill_and_submit_search_form(page):
                    await asyncio.sleep(3)
                    try:
                        await page.wait_for_load_state("networkidle")
                    except Exception:
                        pass
                    await asyncio.sleep(2)

            login_visible = False
            url = page.url.lower()
            if "signin" in url or "shibb" in url or "unauthorized" in url or "/login" in url:
                login_visible = True
            if not login_visible:
                try:
                    if await page.get_by_text("Unauthorized Access").first.is_visible():
                        login_visible = True
                except Exception:
                    pass
            if login_visible:
                print(
                    "Login required. Opening NCLIVE ProQuest Newspapers Library.\n"
                    "Sign in with your credentials. This profile is saved; run the script again after."
                )
                await page.goto(LOGIN_URL_NCLIVE_NEWSPAPERS, wait_until="load", timeout=30_000)
                await asyncio.sleep(3)
                from appstate_login import try_auto_fill_appstate
                if await try_auto_fill_appstate(page):
                    print("Filled login from .env; complete 2FA if prompted.")
                await wait_for_enter_or_timeout(LOGIN_WAIT_SECONDS)
                return

            await page.screenshot(path=str(out_path), full_page=True)
            print("Screenshot saved to:", out_path.resolve())
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
