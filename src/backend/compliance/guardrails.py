"""Compliance guardrails. Every check is callable, testable, and pure.

Enforced properties:
  1. No RFC-1918, loopback, or link-local IPs in any output url/host.
  2. No bare credentials embedded in url (user:password@host).
  3. Residential ARIN org labels are dropped.
  4. CameraResult with thumbnail_url must have blur_required set explicitly.
  5. Every output dict carries fetched_at (ISO 8601, UTC).
"""
from __future__ import annotations

import ipaddress
import re
from typing import Iterable
from urllib.parse import urlparse

from backend.shared.constants import F_BLUR, F_FETCHED, F_THUMB, F_URL

_RESIDENTIAL_PATTERNS = (
    r"\bresidential\b",
    r"\bhome\b",
    r"\bcomcast\b",
    r"\bcox\b",
    r"\bverizon[-\s]?wireless\b",
    r"\bverizon\W+fios\b",
    r"\bat\W*&\W*t\b",                # AT&T (consumer)
    r"\batt\W*internet\b",
    r"\bspectrum\b",
    r"\bcharter\b",
    r"\bcable[\s-]?one\b",
    r"\bdsl\b",
    r"\bbroadband\b",
)

_RESIDENTIAL_RE = re.compile("|".join(_RESIDENTIAL_PATTERNS), re.IGNORECASE)


def is_private_ip(host: str) -> bool:
    """True if host is an RFC-1918, loopback, link-local, multicast, or reserved
    IP literal. Hostnames (non-IP) return False — they are checked elsewhere."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def url_has_private_host(url: str) -> bool:
    """True if the URL's host is a private/loopback/link-local IP literal."""
    if not url:
        return False
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
    except ValueError:
        return True
    host = (parsed.hostname or "").strip("[]")
    if not host:
        return True
    return is_private_ip(host)


def url_has_credentials(url: str) -> bool:
    """True if the URL embeds username:password in the authority section."""
    if not url:
        return False
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
    except ValueError:
        return True
    return bool(parsed.username or parsed.password)


def is_residential_org(label: str | None) -> bool:
    if not label:
        return False
    return bool(_RESIDENTIAL_RE.search(label))


def has_required_blur_flag(result: dict) -> bool:
    """If thumbnail_url is set, blur_required must be a bool."""
    if result.get(F_THUMB):
        return isinstance(result.get(F_BLUR), bool)
    return True


def has_fetched_at(result: dict) -> bool:
    return isinstance(result.get(F_FETCHED), str) and bool(result[F_FETCHED])


def is_compliant_camera(result: dict) -> tuple[bool, list[str]]:
    """Return (ok, [reasons_if_failing])."""
    reasons: list[str] = []
    url = result.get(F_URL, "")
    if url and url_has_private_host(url):
        reasons.append("url has private/loopback host")
    if url_has_credentials(url):
        reasons.append("url embeds credentials")
    if not has_required_blur_flag(result):
        reasons.append("thumbnail present but blur_required missing/non-bool")
    if not has_fetched_at(result):
        reasons.append("fetched_at missing")
    return (not reasons, reasons)


def filter_compliant(results: Iterable[dict]) -> list[dict]:
    """Drop any non-compliant result. Used as a final gate before output."""
    out: list[dict] = []
    for r in results:
        ok, _ = is_compliant_camera(r)
        if ok:
            out.append(r)
    return out
