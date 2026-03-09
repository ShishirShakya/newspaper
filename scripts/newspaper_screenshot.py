"""
Newspapers.com search results screenshot (from newspapers-prompt.md).

Two-phase flow: open the homepage, then fill and submit the search form to reach
the results page. No direct navigation to the results URL (the site redirects it).

Run from project root:
  uv sync
  uv run playwright install chromium
  uv run python scripts/newspaper_screenshot.py

Or in Cursor: use the prompt in newspapers-prompt.md so the agent uses the
browser (Playwright MCP) to do the same steps.

1. Opens the Newspapers.com homepage
2. If login is required, opens NCLIVE; after you sign in and press Enter, the script continues in the same run (goes back to the homepage and proceeds). If the session is still not recognized, it will ask you to run again.
3. Fills and submits the search form (Certificate of Need, NC, 1960-2026)
4. Waits for the results page, then takes a full-page screenshot into newspapers_screenshots/
5. Prints the saved path (or a clear message if form fill failed)
"""

import asyncio

from playwright.async_api import async_playwright

from browser_context import create_persistent_context
from newspapers_config import (
    HOMEPAGE_URL,
    OUTPUT_DIR,
    POST_LOGIN_HOMEPAGE_WAIT_SECONDS,
    USER_DATA_DIR,
)
from newspapers_login import check_login_required, run_login_flow_and_continue
from newspapers_search_form import fill_and_submit_search_form

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
            await page.goto(HOMEPAGE_URL, wait_until="load", timeout=30_000)
            try:
                await page.wait_for_load_state("networkidle")
            except Exception:
                pass  # networkidle best-effort; continue without
            await asyncio.sleep(2)

            if await check_login_required(page):
                print(
                    "Login required. Opening NCLIVE ProQuest Newspapers Library.\n"
                    "Sign in, then press Enter in the terminal to continue."
                )
                if not await run_login_flow_and_continue(page):
                    return
                await asyncio.sleep(POST_LOGIN_HOMEPAGE_WAIT_SECONDS)

            if not await fill_and_submit_search_form(page):
                print(
                    "Could not fill the search form; still on homepage. Log in if needed and run again."
                )
                await asyncio.sleep(5)
                return

            await asyncio.sleep(3)
            try:
                await page.wait_for_load_state("networkidle")
            except Exception:
                pass  # networkidle best-effort; continue without
            await asyncio.sleep(2)

            if "/search/results/" not in page.url:
                print(
                    "Search form did not navigate to results page. Still at: " + page.url
                )
                await asyncio.sleep(5)
                return

            await page.screenshot(path=str(out_path), full_page=True)
            print("Screenshot saved to:", out_path.resolve())
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
