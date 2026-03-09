"""
Fill and submit the Newspapers.com World Collection search form when the script
lands on the search page (e.g. after login) so Keyword, Date, and Location are set.
"""

SEARCH_KEYWORD = "certificate of need"
SEARCH_DATE = "1960-2026"
SEARCH_LOCATION = "North Carolina"


async def _try_fill_by_label_placeholder(page) -> bool:
    """Try filling using label and placeholder selectors."""
    try:
        keyword_input = (
            page.get_by_label("Keyword").or_(
                page.get_by_placeholder("Add a keyword or name")
            ).or_(page.locator('input[placeholder*="keyword"]')).or_(
                page.locator('input[placeholder*="name"]')
            ).first
        )
        if not await keyword_input.is_visible(timeout=2000):
            return False
        await keyword_input.fill(SEARCH_KEYWORD)

        date_input = (
            page.get_by_label("Date (optional)").or_(page.get_by_label("Date")).or_(
                page.get_by_placeholder("Add a date or range")
            ).or_(page.locator('input[placeholder*="date"]')).first
        )
        await date_input.fill(SEARCH_DATE)

        location_input = (
            page.get_by_label("Location (optional)").or_(page.get_by_label("Location")).or_(
                page.get_by_placeholder("Add a city, state, or country")
            ).or_(page.locator('input[placeholder*="city"]')).or_(
                page.locator('input[placeholder*="state"]')
            ).or_(page.locator('input[placeholder*="country"]')).first
        )
        await location_input.fill(SEARCH_LOCATION)

        search_btn = (
            page.get_by_role("button", name="Search").or_(
                page.locator("button[type='submit']")
            ).or_(page.get_by_role("button", name="Search")).or_(
                page.locator("button").filter(has=page.locator("svg")).first
            ).first
        )
        await search_btn.click()
        return True
    except Exception:
        return False


async def fill_and_submit_search_form(page) -> bool:
    """
    If the Newspapers.com search form is visible, fill Keyword, Date, and Location
    and click Search. Returns True if the form was filled and submitted.
    """
    return await _try_fill_by_label_placeholder(page)
