"""
Screenshot every search result for "Certificate of Need" (NC, 1960-2026) and build a CSV index.

Flow: open the Newspapers.com homepage, optional login, then navigate to the search
results URL via SEARCH_URL. Collects all result links by clicking "see more results"
until no more, then screenshots each link and appends a row to the CSV.

Run from project root:
  uv run python scripts/newspaper_screenshot_all.py

Uses the same persistent browser profile as newspaper_screenshot.py. If login is required, after you sign in and press Enter the script continues in the same run; if the session is still not recognized, it will ask you to run again. Resumes from existing CSV/screenshots if interrupted (skips already-done match numbers).
"""

import asyncio
import csv
import re
from pathlib import Path

from playwright.async_api import async_playwright

from browser_context import create_persistent_context
from newspapers_config import (
    ARTICLE_LINK_XPATH,
    CSV_FILENAME,
    GOTO_TIMEOUT_MS,
    HOMEPAGE_URL,
    MAX_SEE_MORE_CLICKS,
    NEWSPAPERS_BASE_URL,
    OUTPUT_DIR,
    RESULTS_CONTAINER_XPATH,
    SCREENSHOT_PREFIX,
    SEE_MORE_BUTTON_TEXT,
    SEE_MORE_VISIBLE_TIMEOUT_MS,
    SEE_MORE_WAIT_SECONDS,
    USER_DATA_DIR,
)
from newspapers_login import check_login_required, run_login_flow_and_continue
from newspapers_navigation import goto_results_page

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


def _normalize_result_url(href: str) -> str | None:
    """Build absolute URL from href using NEWSPAPERS_BASE_URL; return None if not a result link."""
    if not href or "search" in href or "results" in href:
        return None
    href = href.strip()
    if href.startswith("http"):
        return href if "newspapers.com" in href else None
    base = NEWSPAPERS_BASE_URL.rstrip("/")
    return base + (href if href.startswith("/") else "/" + href)


async def _get_result_links_on_page(page) -> list[dict]:
    """Collect result entries on current search results page from the results container. Returns list of {url, ...}."""
    items = []
    seen_hrefs: set[str] = set()
    try:
        container = page.locator("xpath=" + RESULTS_CONTAINER_XPATH)
        links = container.locator("xpath=" + ARTICLE_LINK_XPATH)
        count = await links.count()
        for i in range(count):
            node = links.nth(i)
            href = await node.get_attribute("href")
            url = _normalize_result_url(href or "")
            if not url or url in seen_hrefs:
                continue
            seen_hrefs.add(url)
            try:
                snippet = _sanitize(await node.locator("..").first.text_content() or "", 500)
            except Exception:
                snippet = ""
            items.append({
                "url": url,
                "newspaper_title": "",
                "publication_date": "",
                "page_number": "",
                "location": "",
                "snippet": snippet,
            })
    except Exception:
        # Container or links not found / timeout; return what we have (caller handles empty list).
        pass
    return items


async def _collect_all_result_links(page) -> list[dict]:
    """Collect all result links by repeatedly clicking 'see more results' until no more or max clicks. Returns deduplicated list."""
    seen_hrefs: set[str] = set()
    all_items: list[dict] = []
    stop_reason = f"reached max see-more clicks ({MAX_SEE_MORE_CLICKS})"
    for _ in range(MAX_SEE_MORE_CLICKS):
        batch = await _get_result_links_on_page(page)
        for item in batch:
            url = item.get("url") or ""
            if url and url not in seen_hrefs:
                seen_hrefs.add(url)
                all_items.append(item)
        try:
            btn = page.get_by_text(SEE_MORE_BUTTON_TEXT, exact=False).first
            if not await btn.is_visible(timeout=SEE_MORE_VISIBLE_TIMEOUT_MS):
                stop_reason = "no 'see more' button"
                break
            await btn.scroll_into_view_if_needed()
            await btn.click()
        except Exception:
            # Best-effort: no more button or click failed; continue with whatever links were collected.
            stop_reason = "see more button not found or click failed"
            break
        await asyncio.sleep(SEE_MORE_WAIT_SECONDS)
    print(f"Stopped: {stop_reason}. Collected {len(all_items)} links.")
    return all_items


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
            await page.goto(HOMEPAGE_URL, wait_until="load", timeout=GOTO_TIMEOUT_MS)
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

            if not await goto_results_page(page):
                await asyncio.sleep(5)
                return

            all_results = await _collect_all_result_links(page)
            if not all_results:
                print("No result links found. Check selectors or login.")
                return

            total_processed = 0
            for item in all_results:
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

            print(f"Done. Total recorded: {len(done)}. CSV: {CSV_PATH.resolve()}")
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
