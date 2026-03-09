"""Shared config for Newspapers.com scripts."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEARCH_URL = (
    "https://newscomwc.newspapers.com/search/results/"
    "?date-end=2026&date-start=1842&keyword=%22Certificate+of+Need%22&region=us-nc"
)
# NCLIVE proxy for ProQuest Newspapers Library (sign in here for newspaper access)
LOGIN_URL_NCLIVE_NEWSPAPERS = (
    "https://newspaperslibrary-proquest-com.proxy006.nclive.org/?accountid=8337"
)
LIBRARY_NEWSPAPERS_URL = "https://library.appstate.edu/research/databases/subjects/newspapers"
OUTPUT_DIR = PROJECT_ROOT / "newspapers_screenshots"
USER_DATA_DIR = PROJECT_ROOT / "playwright_browser_data"
# How long to keep the browser open when login is required (seconds); also wait for Enter
LOGIN_WAIT_SECONDS = 600
CSV_FILENAME = "certificate_of_need_nc_results.csv"
SCREENSHOT_PREFIX = "certificate_of_need_nc"
