"""
Helmet (helmet.finna.fi) availability scraper.

Uses the AjaxTab endpoint that the Finna frontend calls to load the holdings
tab. Returns an HTML fragment — no JS rendering needed.

Endpoint:
  POST https://helmet.finna.fi/Record/<id>/AjaxTab
  Body: tab=holdings
  Headers: X-Requested-With: XMLHttpRequest  (required, else 403)

HTML structure of the response:
  div.holdings-group                        — one per library branch
    div.holdings-container-heading
      div.location                          — branch name (after chevron icons)
      div.holdings-details
        span.status-available               — present if ≥1 copy available
        span.status-unavailable             — present if all copies unavailable
"""

import re
import requests
from lxml import html

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
}

# Shared session so cookies persist across requests (same session = no extra
# redirects, and the site may set a session cookie on first load).
_session = requests.Session()
_session.headers.update(HEADERS)


# ---------------------------------------------------------------------------
# URL → AjaxTab URL
# ---------------------------------------------------------------------------

def _ajax_url(page_url: str) -> str:
    """
    https://helmet.finna.fi/Record/helmet.2369709      →
    https://helmet.finna.fi/Record/helmet.2369709/AjaxTab
    """
    return page_url.rstrip("/") + "/AjaxTab"


# ---------------------------------------------------------------------------
# Shared fetch
# ---------------------------------------------------------------------------

def _fetch_holdings_tree(page_url: str) -> html.HtmlElement:
    resp = _session.post(
        _ajax_url(page_url),
        data={"tab": "holdings"},
        timeout=15,
    )
    resp.raise_for_status()
    return html.fromstring(resp.text)


# ---------------------------------------------------------------------------
# Helper: extract branch name from a holdings-group element
# ---------------------------------------------------------------------------

def _branch_name(group: html.HtmlElement) -> str:
    """
    The .location div contains icon <span>s followed by a text node with the
    branch name, e.g. "  Lippulaiva aik  ". Strip and return it.
    """
    loc = group.cssselect("div.holdings-container-heading div.location")
    if not loc:
        return ""
    # text_content() gives everything; we want only the trailing text node
    # (after the icon spans). Grab all text nodes, take the last non-empty one.
    texts = [t.strip() for t in loc[0].itertext() if t.strip()]
    return texts[-1] if texts else ""


# ---------------------------------------------------------------------------
# 1. Discover libraries for /add
# ---------------------------------------------------------------------------

def fetch_libraries(url: str) -> list[str]:
    """
    Return sorted list of branch names found in the holdings tab.
    """
    tree = _fetch_holdings_tree(url)
    groups = tree.cssselect("div.holdings-group")
    names = []
    for g in groups:
        name = _branch_name(g)
        if name:
            names.append(name)
    return sorted(set(names))


# ---------------------------------------------------------------------------
# 2. Check availability for scheduler / /check_now
# ---------------------------------------------------------------------------

def check_availability(url: str, libraries: list[str]) -> dict[str, dict]:
    """
    Return {branch_name: {"available": bool, "due_date": str|None}}

    due_date is the text after "Lahin erapaiva" in the status span when
    unavailable, e.g. "8.6.2026". None when available or no date shown.
    """
    tree = _fetch_holdings_tree(url)
    groups = tree.cssselect("div.holdings-group")

    availability_map: dict[str, dict] = {}
    for g in groups:
        name = _branch_name(g)
        if not name:
            continue
        heading = g.cssselect("div.holdings-container-heading")
        if not heading:
            continue

        available = bool(heading[0].cssselect("span.status-available"))

        due_date = None
        if not available:
            status_spans = heading[0].cssselect("span.status-unavailable")
            for span in status_spans:
                text = span.text_content().strip()
                # "Lahin erapaiva 8.6.2026" or "Lahin erapaiva 8.6.2026"
                import re
                match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", text)
                if match:
                    due_date = match.group(1)
                    break

        # OR across copies: if any entry for this branch is available, mark available
        existing = availability_map.get(name)
        if existing is None:
            availability_map[name] = {"available": available, "due_date": due_date}
        elif available:
            availability_map[name] = {"available": True, "due_date": None}

    results: dict[str, dict] = {}
    for lib in libraries:
        results[lib] = availability_map.get(lib, {"available": False, "due_date": None})

    return results
