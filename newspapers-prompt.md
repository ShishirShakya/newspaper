# Newspapers.com Screenshot (Python, Playwright, Cursor)

Use **Cursor** with **Playwright MCP** when the browser is available, or run the Python script locally.

## In Cursor (Playwright MCP)

When Playwright MCP is configured, use this prompt so the agent drives the browser:

## Prompt

```
Use the browser to:
1. Go to: https://newscomwc.newspapers.com/search/results/?date-end=2026&date-start=1842&keyword=%22Certificate+of+Need%22&region=us-nc
2. Wait for the page to fully load (search results and map visible).
3. Take a full-page screenshot and save it to a file in my workspace (e.g. under a folder like `newspapers_screenshots` or in the CONLAW folder). Use a clear filename like `certificate_of_need_nc_search_1842_2026.png`.
4. Tell me the exact path where the screenshot was saved.

If the page shows a login wall, tell me that I need to log in first in this browser session, then I'll ask you to run the same steps again.
```

## Python script (no MCP)

From the project root (with uv):

```bash
uv sync
uv run playwright install chromium
uv run python scripts/newspaper_screenshot.py
```

Search is **"Certificate of Need"**, **1842–2026**, **North Carolina**. Screenshots go to `newspapers_screenshots/` (e.g. `certificate_of_need_nc_search_1842_2026.png`). To capture **all 591 matches** one by one with a CSV index, run `uv run python scripts/newspaper_screenshot_all.py` (see below). The script uses a **persistent browser profile** (`playwright_browser_data/`): log in once in the script’s browser (same account as in Chrome, or open your institution’s library site in that browser and reach Newspapers.com from there), then run the script again; the session is reused on future runs.

## Notes

- **Login (script):** If you get "Unauthorized Access," the script opens the [NCLIVE ProQuest Newspapers Library](https://newspaperslibrary-proquest-com.proxy006.nclive.org/?accountid=8337). Sign in with your credentials. The profile is saved in `playwright_browser_data/`; run the script again after. Optional: copy `.env.example` to `.env` and set `APPSTATE_LOGIN` and `APPSTATE_PASSWORD` so the script can auto-fill the App State form (you may still need to complete 2FA). Never commit `.env`.
- **"Not a robot" / CAPTCHA:** The scripts use anti-detection (playwright-stealth, disabled automation flags, realistic user-agent) to reduce repeated checkbox challenges. If you still see the challenge, complete it once; the persistent profile may be trusted for later runs.
- **Login (MCP):** If you see a Newspapers.com login page in the MCP browser, log in once there, then run the same prompt again.
- **Screenshot all 591 matches + CSV:** Run `uv run python scripts/newspaper_screenshot_all.py`. It opens each result in turn, takes a full-page screenshot (`certificate_of_need_nc_0001.png`, `0002.png`, …), and appends a row to `newspapers_screenshots/certificate_of_need_nc_results.csv` with columns: `match_number`, `url`, `newspaper_title`, `publication_date`, `page_number`, `location`, `snippet`, `screenshot_path`. You can search/filter the CSV to find relevant context. If the run is interrupted, run the script again to resume (already-done match numbers are skipped).
- **Other searches:** Change the URL (keyword, date range, region) to screenshot different search result pages.
- **Output folder:** In Cursor MCP settings you can set `--output-dir` for Playwright (e.g. `./newspapers_screenshots`) so screenshots go to a consistent location.
