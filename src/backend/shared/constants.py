"""Shared field names and source identifiers.

Use these constants instead of hardcoded strings anywhere a source name or a
normalized response field is referenced. Changing the value here changes it
everywhere.
"""
from __future__ import annotations

USER_AGENT = "GRIDLAND/0.1 (+https://github.com/nitepoetlaureate/GRIDLAND8)"

# Discovery source identifiers
SRC_OSM = "osm"
SRC_FCC = "fcc"
SRC_MAPILLARY = "mapillary"
SRC_CRTSH = "crtsh"
SRC_CALTRANS = "caltrans"
SRC_WSDOT = "wsdot"
SRC_N511NY = "n511ny"
SRC_LIVECAM = "livecam"
SRC_NYCTMC = "nyctmc"
SRC_CR511 = "castlerock_511"
SRC_NPS = "nps_webcams"

# Publication status of a result's underlying source
PUB_OPERATOR_PUBLISHED = "operator_published"
PUB_DIRECTORY_LISTED = "directory_listed"
PUB_CROWDSOURCED = "crowdsourced"

# Normalized response field names
F_ID = "id"
F_LAT = "lat"
F_LON = "lon"
F_SOURCE = "source"
F_LABEL = "label"
F_URL = "url"
F_THUMB = "thumbnail_url"
F_BLUR = "blur_required"
F_AGE = "data_age_s"
F_FETCHED = "fetched_at"

# Realtime entity types
ENT_AIRCRAFT = "aircraft"
ENT_SATELLITE = "satellite"
ENT_SHIP = "ship"
ENT_LIGHTNING = "lightning"
ENT_TRANSIT = "transit"

# WebSocket message envelope keys
WS_TYPE = "type"
WS_PAYLOAD = "payload"
WS_TS = "ts"
