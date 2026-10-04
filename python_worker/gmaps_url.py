"""Wyciąganie lokalizacji z linku Map Google, współrzędnych lub adresu."""
import re
from urllib.parse import unquote, unquote_plus

import requests

_NUM = r"(-?\d{1,3}\.\d+)"
_PATTERNS = [
    re.compile(rf"!3d{_NUM}!4d{_NUM}"),                  # dokładny punkt miejsca (ma pierwszeństwo)
    re.compile(rf"@{_NUM},{_NUM}"),                      # widok mapy
    re.compile(rf"[?&](?:q|ll|query|center|destination)={_NUM}(?:,|%2C)\s*{_NUM}"),
    re.compile(rf"^\s*{_NUM}\s*[,; ]\s*{_NUM}\s*$"),     # goła para
]
_SHORT_HOSTS = ("maps.app.goo.gl", "goo.gl/maps", "g.co/kgs")
_PLACE_RE = re.compile(r"/maps/place/([^/@?]+)")
_SEARCH_RE = re.compile(r"/maps/search/([^/@?]+)")


def _valid(lat: float, lon: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180


def _extract_coords(text: str):
    for pat in _PATTERNS:
        m = pat.search(text)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if _valid(lat, lon):
                return lat, lon
    return None


def _extract_label(url: str):
    m = _PLACE_RE.search(url) or _SEARCH_RE.search(url)
    if m:
        label = unquote_plus(m.group(1)).strip()
        if label and not re.fullmatch(r"-?\d+\.\d+,\s*-?\d+\.\d+", label):
            return label
    return None


def _expand_short_url(url: str) -> str:
    try:
        resp = requests.get(url, allow_redirects=True, timeout=8,
                            headers={"User-Agent": "Mozilla/5.0"})
        return resp.url or url
    except requests.RequestException:
        return url


def parse_gmaps_location(text: str, geocoder=None) -> dict | None:
    """Zwraca {'lat','lon','label'} albo None.

    `geocoder` to callable(address) -> (lat, lon) używany tylko, gdy w linku nie
    ma współrzędnych, a jest nazwa miejsca lub zwykły adres.
    """
    text = (text or "").strip()
    if not text:
        return None

    if text.startswith("http") and any(h in text for h in _SHORT_HOSTS):
        text = _expand_short_url(text)

    decoded = unquote(text)
    coords = _extract_coords(decoded)
    label = _extract_label(text) if text.startswith("http") else None
    if coords:
        return {"lat": coords[0], "lon": coords[1], "label": label}

    address = label or (None if text.startswith("http") else text)
    if address and geocoder:
        lat, lon = geocoder(address)
        if lat is not None and lon is not None:
            return {"lat": lat, "lon": lon, "label": address}
    return None
