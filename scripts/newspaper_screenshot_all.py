"""
Screenshot every search result for "Certificate of Need" (NC, 1960-2026) and build a CSV index.

Run from project root:
  uv run python scripts/newspaper_screenshot_all.py

Uses the same persistent browser profile as newspaper_screenshot.py. Log in first if needed.
Resumes from existing CSV/screenshots if interrupted (skips already-done match numbers).
"""

import asyncio
import csv
import re
from pathlib import Path

from playwright.async_api import async_playwright

from browser_context import create_persistent_context, wait_for_enter_or_timeout
from newspapers_config import (
    CSV_FILENAME,
    LOGIN_URL_NCLIVE_NEWSPAPERS,
    LOGIN_WAIT_SECONDS,
    OUTPUT_DIR,
    SCREENSHOT_PREFIX,
    SEARCH_URL,
    USER_DATA_DIR,
)

CSV_PATH = OUTPUT_DIR / CSV_FILENAME
CSV_COLUMNS = [
    "match_number",
    "url",
    "newspaper_title",
    "publication_date",
    "page_number",
    "location",
    "snippet",
    "screenshot_path",
]
DELAY_BETWEEN_ITEMS = 2.0
DELAY_BETWEEN_PAGES = 3.0


def _sanitize(s: str, max_len: int = 200) -> str:
    if not s:
        return ""
    s = re.sub(r"[\r\n\t]", " ", s).strip()
    return s[:max_len] if len(s) > max_len else s


def _load_done_match_numbers() -> set[int]:
    if not CSV_PATH.exists():
        return set()
    done = set()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                done.add(int(row["match_number"]))
            except (ValueError, KeyError):
                continue
    return done


def _ensure_csv_header() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def _append_csv_row(row: dict) -> None:
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)


async def _check_login_required(page) -> bool:
    """True only when we are clearly blocked: Unauthorized Access or on a login/signin URL."""
    url = page.url.lower()
    if "signin" in url or "shibb" in url or "unauthorized" in url or "/login" in url:
        return True
    try:
        if await page.get_by_text("Unauthorized Access").first.is_visible():
            return True
    except Exception:
        pass
    return False


async def _get_result_links_on_page(page) -> list[dict]:
    """Collect result entries on current search results page. Returns list of {url, title, date, page, location, snippet}."""
    items = []
    # Result links often go to /image/ or similar viewer URLs; result cards may be in a list or grid
    locators = [
        page.locator('a[href*="/image/"]'),
        page.locator('a[href*="/viewer/"]'),
        page.locator("[data-search-result] a[href]"),
        page.locator(".search-result a[href]"),
        page.locator("article a[href*='newspapers.com']"),
    ]
    seen_hrefs = set()
    for loc in locators:
        try:
            count = await loc.count()
            for i in range(count):
                node = loc.nth(i)
                href = await node.get_attribute("href")
                if not href or href in seen_hrefs:
                    continue
                if "newspapers.com" not in href and not href.startswith("/"):
                    continue
                if not href.startswith("http"):
                    href = "https://newscomwc.newspapers.com" + (href if href.startswith("/") else "/" + href)
                seen_hrefs.add(href)
                title = _sanitize(await node.locator("..").first.text_content() or "")
                if len(title) > 300:
                    title = title[:300] + "..."
                items.append({
                    "url": href,
                    "newspaper_title": "",
                    "publication_date": "",
                    "page_number": "",
                    "location": "",
                    "snippet": title,
                })
            if items:
                break
        except Exception:
            continue
    return items


async def _click_next_page(page) -> bool:
    """Click Next pagination if present. Returns True if clicked."""
    for selector in [
        'button:has-text("Next")',
        'a:has-text("Next")',
        '[aria-label="Next page"]',
        'a[rel="next"]',
        ".pagination a.next",
        "a.next",
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible():
                await btn.click()
                await asyncio.sleep(DELAY_BETWEEN_PAGES)
                return True
        except Exception:
            continue
    return False


async def main() -> None:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_csv_header()
    done = _load_done_match_numbers()
    if done:
        print(f"Resuming: {len(done)} already in CSV; will skip those and process the rest.")
    global_index = 0  # 1-based match_number = global_index after increment

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

            if await _check_login_required(page):
                print(
                    "Login required. Opening NCLIVE ProQuest Newspapers Library.\n"
                    "Sign in with your credentials, then run this script again."
                )
                await page.goto(LOGIN_URL_NCLIVE_NEWSPAPERS, wait_until="load", timeout=30_000)
                await asyncio.sleep(3)
                from appstate_login import try_auto_fill_appstate
                if await try_auto_fill_appstate(page):
                    print("Filled login from .env; complete 2FA if prompted.")
                await wait_for_enter_or_timeout(LOGIN_WAIT_SECONDS)
                return

            total_processed = 0
            page_num = 1
            while True:
                results = await _get_result_links_on_page(page)
                if not results:
                    # Fallback: try clicking each visible result link one by one by collecting hrefs
                    all_links = await page.locator('a[href*="newspapers.com"]').evaluate_all(
                        "nodes => nodes.map(n => ({ href: n.href, text: n.textContent?.slice(0,200) || '' }))"
                    )
                    seen = set()
                    for info in all_links:
                        href = (info.get("href") or "").strip()
                        if not href or "results" in href or "search" in href or href in seen:
                            continue
                        seen.add(href)
                        results.append({
                            "url": href,
                            "newspaper_title": _sanitize(info.get("text", ""), 300),
                            "publication_date": "",
                            "page_number": "",
                            "location": "",
                            "snippet": "",
                        })
                    results = results[:50]

                for item in results:
                    global_index += 1
                    match_number = global_index
                    if match_number in done:
                        continue
                    url = item.get("url") or ""
                    if not url:
                        continue
                    screenshot_name = f"{SCREENSHOT_PREFIX}_{match_number:04d}.png"
                    screenshot_path = OUTPUT_DIR / screenshot_name
                    try:
                        await page.goto(url, wait_until="load", timeout=25_000)
                        await asyncio.sleep(1.5)
                        await page.screenshot(path=str(screenshot_path), full_page=True)
                        row = {
                            "match_number": match_number,
                            "url": url,
                            "newspaper_title": _sanitize(item.get("newspaper_title", "")),
                            "publication_date": _sanitize(item.get("publication_date", "")),
                            "page_number": _sanitize(item.get("page_number", "")),
                            "location": _sanitize(item.get("location", "")),
                            "snippet": _sanitize(item.get("snippet", ""), 500),
                            "screenshot_path": str(screenshot_path.resolve()),
                        }
                        _append_csv_row(row)
                        done.add(match_number)
                        total_processed += 1
                        print(f"  {total_processed}: match {match_number} -> {screenshot_path.name}")
                    except Exception as e:
                        print(f"  Skip match {match_number}: {e}")
                    await asyncio.sleep(DELAY_BETWEEN_ITEMS)

                has_next = await _click_next_page(page)
                if not has_next:
                    break
                page_num += 1

            print(f"Done. Total recorded: {len(done)}. CSV: {CSV_PATH.resolve()}")
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
