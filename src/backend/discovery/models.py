"""Normalized discovery models."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


SourceName = Literal[
    "osm", "fcc", "mapillary", "crtsh",
    "caltrans", "wsdot", "n511ny",
    "livecam",
    "nyctmc", "castlerock_511", "nps_webcams",
    "penndot", "cam2",
]

PublicationStatus = Literal[
    "operator_published",   # the operator publishes the feed as a public asset
    "directory_listed",     # listed in a public registry/dataset (e.g., OSM tag)
    "crowdsourced",         # community-contributed listing
]


class CameraResult(BaseModel):
    """A single normalized camera or surveillance device."""
    id: str
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    source: SourceName
    publication_status: PublicationStatus = "directory_listed"
    label: str
    url: str = ""
    thumbnail_url: str | None = None
    blur_required: bool = True
    data_age_s: int = 0
    fetched_at: str
    tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def url_no_creds(cls, v: str) -> str:
        if not v:
            return v
        try:
            authority = v.split("://", 1)[-1].split("/", 1)[0]
        except Exception:
            return v
        if "@" in authority:
            raise ValueError("url contains embedded credentials")
        return v


class DiscoveryResponse(BaseModel):
    query: dict
    results: list[CameraResult]
    fetched_at: str
    counts_by_source: dict[str, int]
