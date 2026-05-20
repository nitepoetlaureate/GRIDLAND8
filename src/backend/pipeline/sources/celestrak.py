"""Celestrak TLE catalog fetcher.

Returns a list of {name, line1, line2} entries for a given group, where group
is one of `tle_catalogs` in settings (e.g. "stations", "active", "starlink",
"weather", "geo").

Celestrak guidance: cache aggressively. We default to 6-hour TTL.
"""
from __future__ import annotations

import logging

import httpx

from backend.settings import get_settings
from backend.shared.cache import default_cache, make_key
from backend.shared.constants import USER_AGENT

log = logging.getLogger(__name__)

GP_URL = "https://celestrak.org/NORAD/elements/gp.php"


def parse_tle_text(text: str) -> list[dict]:
    """Parse the classic 3-line TLE format into structured entries."""
    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: list[dict] = []
    i = 0
    while i + 2 < len(lines) + 1:
        if i + 2 >= len(lines):
            break
        name, l1, l2 = lines[i], lines[i + 1], lines[i + 2]
        if l1.startswith("1 ") and l2.startswith("2 "):
            out.append({"name": name, "line1": l1, "line2": l2})
            i += 3
        else:
            i += 1
    return out


async def _fetch_tle(group: str) -> str:
    s = get_settings()
    cache = default_cache()
    params = {"GROUP": group, "FORMAT": "tle"}
    key = make_key("GET", GP_URL, params=params) + "|tle"

    async def loader() -> str | None:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(s.http_timeout_s),
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
            ) as c:
                r = await c.get(GP_URL, params=params)
                if r.status_code != 200:
                    return None
                return r.text
        except Exception as e:
            log.warning("Celestrak fetch failed (%s): %s", group, e)
            return None

    val = await cache.get_or_fetch(key, s.cache_ttl_tle_s, loader)
    return val or ""


async def catalog(group: str) -> list[dict]:
    s = get_settings()
    if group not in s.tle_catalogs:
        return []
    text = await _fetch_tle(group)
    return parse_tle_text(text)
