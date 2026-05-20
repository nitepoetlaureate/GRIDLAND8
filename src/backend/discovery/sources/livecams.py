"""Curated registry of operator-published live cams (NPS, USGS, Explore.org,
Cornell Bird Cams, etc.). Returned when the user's search circle encompasses
the cam's coordinates.

Adding a cam: add a row to LIVECAMS below. All entries must point at a feed
the operator publishes on their own site as a public asset. We do not scrape
embed URLs; we link to the operator's own viewing page (which they invite
the public to load).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from backend.discovery.models import CameraResult
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_LIVECAM
from backend.shared.http import utc_now_iso


@dataclass(frozen=True)
class LiveCam:
    id: str
    name: str
    lat: float
    lon: float
    url: str
    thumbnail_url: str | None
    operator: str
    category: str   # nature | parks | weather | observatory | civic


LIVECAMS: tuple[LiveCam, ...] = (
    # ── US National Park Service ────────────────────────────────────────────
    LiveCam("nps_yellowstone_old_faithful", "Old Faithful Geyser",
            44.4605, -110.8281,
            "https://www.nps.gov/yell/learn/photosmultimedia/webcams.htm",
            None, "US National Park Service", "parks"),
    LiveCam("nps_yosemite_elcapitan", "El Capitan",
            37.7341, -119.6377,
            "https://www.nps.gov/yose/learn/photosmultimedia/webcams.htm",
            None, "US National Park Service", "parks"),
    LiveCam("nps_glacier_bay", "Glacier Bay",
            58.4554, -135.8946,
            "https://www.nps.gov/glba/learn/photosmultimedia/webcams.htm",
            None, "US National Park Service", "parks"),

    # ── USGS Volcano Observatories ──────────────────────────────────────────
    LiveCam("usgs_kilauea", "Kīlauea Summit",
            19.4069, -155.2834,
            "https://www.usgs.gov/volcanoes/kilauea/webcams",
            None, "USGS Hawaiian Volcano Observatory", "observatory"),
    LiveCam("usgs_mt_st_helens", "Mount St. Helens",
            46.1912, -122.1944,
            "https://www.usgs.gov/volcanoes/mount-st.-helens/webcams",
            None, "USGS Cascades Volcano Observatory", "observatory"),
    LiveCam("usgs_yellowstone_caldera", "Yellowstone Caldera",
            44.4280, -110.5885,
            "https://www.usgs.gov/volcanoes/yellowstone/webcams",
            None, "USGS Yellowstone Volcano Observatory", "observatory"),

    # ── Cornell Lab of Ornithology Bird Cams ────────────────────────────────
    LiveCam("cornell_redtailed_hawks", "Cornell Red-Tailed Hawks",
            42.4477, -76.4762,
            "https://www.allaboutbirds.org/cams/cornell-hawks/",
            None, "Cornell Lab of Ornithology", "nature"),
    LiveCam("cornell_panama_fruit_feeder", "Panama Fruit Feeder",
            8.6622, -82.7783,
            "https://www.allaboutbirds.org/cams/panama-fruit-feeders/",
            None, "Cornell Lab of Ornithology", "nature"),

    # ── Explore.org ─────────────────────────────────────────────────────────
    LiveCam("explore_katmai_brown_bears", "Brooks Falls Brown Bears",
            58.5613, -155.7798,
            "https://explore.org/livecams/brown-bears/brown-bear-salmon-cam-brooks-falls",
            None, "Explore.org / Katmai NP", "nature"),
    LiveCam("explore_decorah_eagles", "Decorah Eagles",
            43.3061, -91.7847,
            "https://explore.org/livecams/raptor-resource-project/decorah-eagles",
            None, "Explore.org / Raptor Resource Project", "nature"),
    LiveCam("explore_seal_haulout", "Pacific Northwest Seal Cam",
            48.4960, -124.7290,
            "https://explore.org/livecams/oceans/orcalab-base",
            None, "Explore.org", "nature"),

    # ── Smithsonian National Zoo ────────────────────────────────────────────
    LiveCam("si_zoo_elephant", "Smithsonian Elephant Cam",
            38.9296, -77.0497,
            "https://nationalzoo.si.edu/webcams/elephant-cam",
            None, "Smithsonian National Zoo", "nature"),
    LiveCam("si_zoo_lion", "Smithsonian Lion Cam",
            38.9296, -77.0497,
            "https://nationalzoo.si.edu/webcams/lion-cam",
            None, "Smithsonian National Zoo", "nature"),

    # ── Monterey Bay Aquarium ───────────────────────────────────────────────
    LiveCam("mbayaq_kelp", "Monterey Bay Kelp Forest",
            36.6181, -121.9019,
            "https://www.montereybayaquarium.org/animals/live-cams/kelp-forest-cam",
            None, "Monterey Bay Aquarium", "nature"),
    LiveCam("mbayaq_jellies", "Monterey Bay Jellies",
            36.6181, -121.9019,
            "https://www.montereybayaquarium.org/animals/live-cams/jelly-cam",
            None, "Monterey Bay Aquarium", "nature"),

    # ── NASA / Space ────────────────────────────────────────────────────────
    LiveCam("nasa_iss_live", "ISS Live (NASA)",
            0.0, 0.0,  # not a fixed point; included as a global anchor
            "https://www.nasa.gov/multimedia/nasatv/iss_ustream.html",
            None, "NASA", "observatory"),
)


def _in_bbox(lat: float, lon: float, c_lat: float, c_lon: float,
             dlat: float, dlon: float) -> bool:
    return abs(lat - c_lat) <= dlat and abs(lon - c_lon) <= dlon


def normalize(entries: tuple[LiveCam, ...], lat: float, lon: float,
              radius_km: float, *, include_global: bool = True) -> list[CameraResult]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    now = utc_now_iso()
    out: list[CameraResult] = []
    for e in entries:
        is_global = e.lat == 0.0 and e.lon == 0.0
        if is_global:
            if not include_global:
                continue
        elif not _in_bbox(e.lat, e.lon, lat, lon, dlat, dlon):
            continue
        try:
            cam = CameraResult(
                id=f"livecam_{e.id}",
                lat=lat if is_global else e.lat,
                lon=lon if is_global else e.lon,
                source=SRC_LIVECAM,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=e.name,
                url=e.url,
                thumbnail_url=e.thumbnail_url,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={"operator": e.operator, "category": e.category,
                      "global": "1" if is_global else "0"},
            )
        except Exception:
            continue
        out.append(cam)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    return normalize(LIVECAMS, lat, lon, radius_km, include_global=False)
