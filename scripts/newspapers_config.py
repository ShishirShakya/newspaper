"""Shared config for Newspapers.com scripts."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Homepage: scripts go here first, then fill and submit the search form to reach results.
HOMEPAGE_URL = "https://newscomwc.newspapers.com/"
# Seconds to wait for the search form keyword input to be visible (form module uses this * 1000 for Playwright ms).
FORM_WAIT_TIMEOUT = 15
# Seconds to wait after returning from login before attempting form fill, so the homepage can render the form.
POST_LOGIN_HOMEPAGE_WAIT_SECONDS = 8
# Reference only (e.g. docstrings); scripts do not use this for initial goto (site redirects to homepage).
SEARCH_URL = (
    "https://newscomwc.newspapers.com/search/results/"
    "?date-end=2026&date-start=1960&keyword=%22certificate+of+need%22&region=us-nc&sort=paper-date-asc"
)
# NCLIVE proxy for ProQuest Newspapers Library (sign in here for newspaper access)
LOGIN_URL_NCLIVE_NEWSPAPERS = (
    "https://newspaperslibrary-proquest-com.proxy006.nclive.org/?accountid=8337"
)
LIBRARY_NEWSPAPERS_URL = "https://library.appstate.edu/research/databases/subjects/newspapers"
OUTPUT_DIR = PROJECT_ROOT / "newspapers_screenshots"
USER_DATA_DIR = PROJECT_ROOT / "playwright_browser_data"
# How long to keep the browser open when login is required (seconds); also wait for Enter. 86400 = 24 hours.
LOGIN_WAIT_SECONDS = 86400
CSV_FILENAME = "certificate_of_need_nc_results.csv"
SCREENSHOT_PREFIX = "certificate_of_need_nc"

# Search results page: container and link selectors, base URL, "see more" pagination.
NEWSPAPERS_BASE_URL = "https://newscomwc.newspapers.com"  # No trailing slash; used to normalize relative hrefs.
RESULTS_CONTAINER_XPATH = "//main/div/div/div[3]"  # Holds result cards and "see more" controls.
ARTICLE_LINK_XPATH = ".//div/div/div[2]/div/a"  # Relative to container; one link per result card.
SEE_MORE_BUTTON_TEXT = "see more results"  # Text to match pagination control (get_by_text).
SEE_MORE_WAIT_SECONDS = 3  # Wait after each "see more" click before re-collecting links.
MAX_SEE_MORE_CLICKS = 50  # Safety cap to avoid infinite loop if button never disappears.
