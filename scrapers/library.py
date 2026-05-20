"""
Library page scraper.

Two responsibilities:
1. fetch_libraries(url)  → list[str]
   Parse the page and return all library names found in the availability table.
   Used during /add so the user can pick which libraries to track.

2. check_availability(url, libraries) → dict[str, bool]
   Return {library_name: is_available} for the requested libraries.
   is_available = True means the item is ready to borrow (green status).

Both functions are sync; call them from async code via asyncio.to_thread().

TODO: fill in real XPaths / CSS selectors / regex patterns once the target
      library system's markup is known.
"""

import requests
from lxml import html


# ---------------------------------------------------------------------------
# Shared fetch helper
# ---------------------------------------------------------------------------

def _fetch_tree(url: str) -> html.HtmlElement:
    """Download page and return an lxml element tree."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LibraryBot/1.0)"
        )
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return html.fromstring(resp.content)


# ---------------------------------------------------------------------------
# 1. Discover libraries on the page
# ---------------------------------------------------------------------------

def fetch_libraries(url: str) -> list[str]:
    """
    Return a list of library branch names found on the availability page.

    TODO: replace the placeholder XPath below with the real one.
    Example (generic): '//table[@class="availability"]//tr/td[1]/text()'
    """
    tree = _fetch_tree(url)

    # ---- PLACEHOLDER — replace with real XPath ----
    LIBRARY_NAME_XPATH = "//TODO"
    # -----------------------------------------------

    names = tree.xpath(LIBRARY_NAME_XPATH)
    return [n.strip() for n in names if n.strip()]


# ---------------------------------------------------------------------------
# 2. Check availability for selected libraries
# ---------------------------------------------------------------------------

def check_availability(url: str, libraries: list[str]) -> dict[str, bool]:
    """
    Return {library_name: is_available} for each library in *libraries*.

    is_available is True when the status cell contains a green/available
    indicator (exact check defined by STATUS_AVAILABLE_PATTERN below).

    TODO: replace XPaths and the status pattern with real values.
    """
    tree = _fetch_tree(url)

    # ---- PLACEHOLDER — replace with real XPaths / patterns ----
    # XPath that, given a library name, finds its status cell text.
    # Many library systems use a <tr> per branch; adapt as needed.
    ROW_XPATH = "//TODO/tr"          # XPath to each availability row
    LIBRARY_CELL_INDEX = 0           # column index of the branch name
    STATUS_CELL_INDEX  = 1           # column index of the status text/class

    # Text or class value that means "available now"
    STATUS_AVAILABLE_PATTERN = "TODO_available_keyword"
    # ------------------------------------------------------------

    results: dict[str, bool] = {}
    rows = tree.xpath(ROW_XPATH)

    for row in rows:
        cells = row.xpath(".//td")
        if len(cells) <= max(LIBRARY_CELL_INDEX, STATUS_CELL_INDEX):
            continue

        branch = cells[LIBRARY_CELL_INDEX].text_content().strip()
        if branch not in libraries:
            continue

        status_text = cells[STATUS_CELL_INDEX].text_content().strip()
        results[branch] = STATUS_AVAILABLE_PATTERN in status_text

    # Any tracked library not found on page → treat as unavailable
    for lib in libraries:
        results.setdefault(lib, False)

    return results
