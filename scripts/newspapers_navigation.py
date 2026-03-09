"""
Navigate to the Newspapers.com search results page. Used by scripts after
initial load and optional login so they reach the results URL without filling the form.
"""

import asyncio

from newspapers_config import (
    GOTO_TIMEOUT_MS,
    RESULTS_PAGE_WAIT_SECONDS,
    SEARCH_URL,
)


async def goto_results_page(page) -> bool:
    """
    Navigate to SEARCH_URL, wait for the page to settle, and verify we are on the
    results page. Return True if "/search/results/" is in page.url; otherwise
    print a message and return False. On navigation timeout or error, print a
    clear message and return False.
    """
    try:
        await page.goto(SEARCH_URL, wait_until="load", timeout=GOTO_TIMEOUT_MS)
    except Exception:
        print("Could not load results page. Check network or login.")
        return False
    try:
        await page.wait_for_load_state("networkidle")
    except Exception:
        pass  # networkidle best-effort; continue without
    await asyncio.sleep(RESULTS_PAGE_WAIT_SECONDS)
    if "/search/results/" in page.url:
        return True
    print("Did not reach results page. Still at: " + page.url)
    return False
