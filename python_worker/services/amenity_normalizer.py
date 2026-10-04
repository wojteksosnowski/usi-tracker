"""Normalizacja i kanonizacja etykiet udogodnień z różnych portali (RP / OTO / TO).

Katalog: python_worker/data/amenity_catalog.json (budowany przez scripts/build_amenity_catalog.py).
"""
import json
import logging
import re
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "amenity_catalog.json"

_NEGATIVE_VALUES = {"nie", "brak", "false", "0", "no"}
_POSITIVE_VALUES = {"tak", "true", "yes", "1"}
_PAREN_RE = re.compile(r"\([^)]*\)")
# przecinek rozdziela tagi, chyba że jest dziesiętny (cyfra po obu stronach)
_COMMA_SPLIT_RE = re.compile(r"(?<!\d),|,(?!\d)")


@lru_cache(maxsize=1)
def load_catalog():
    """Zwraca {'concepts': {id: concept}, 'aliases': {alias: id}, 'phrases': [(regex, id)] (najdłuższe pierwsze),
    'noise': [compiled], 'order': {id: idx}}."""
    concepts, aliases, noise, order = {}, {}, [], {}
    raw = {}
    if not CATALOG_PATH.exists():
        logger.error("Brak katalogu udogodnień: %s", CATALOG_PATH)
    else:
        try:
            raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Nie można wczytać katalogu udogodnień: %s", e)
    for idx, c in enumerate(raw.get("concepts", [])):
        concepts[c["id"]] = c
        order[c["id"]] = idx
        for a in [c["label"], *c.get("aliases", [])]:
            aliases.setdefault(a.strip().lower(), c["id"])
    noise = [re.compile(p) for p in raw.get("noise", [])]
    phrases = [
        (re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)"), cid)
        for a, cid in sorted(aliases.items(), key=lambda kv: -len(kv[0]))
        if len(a) >= 5
    ]
    return {"concepts": concepts, "aliases": aliases, "phrases": phrases, "noise": noise, "order": order}


def normalize_label(raw) -> str:
    """lower, NBSP/zero-width -> spacja, bez nawiasów z wymiarami, zwinięte spacje."""
    if not isinstance(raw, str):
        return ""
    s = raw.replace("\xa0", " ").replace("​", " ").replace("&nbsp;", " ").lower()
    s = _PAREN_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip(" \t\n.;()")
    return s


def _is_noise(s: str, noise) -> bool:
    return (not s) or s.isdigit() or any(p.match(s) for p in noise)


def split_label(raw, noise=None) -> list:
    """Rozbija etykietę na pojedyncze znormalizowane tagi.

    'Winda: tak' -> ['winda'];  'garaż: hala garażowa, parking naziemny' -> ['hala garażowa', 'parking naziemny'];
    'termin oddania: iv kwartał 2027' -> ['termin oddania: iv kwartał 2027'] (zostaje całość, wyłapie ją szum);
    'taras (12,27 m²), ogródek' -> ['taras', 'ogródek'].
    """
    if noise is None:
        noise = load_catalog()["noise"]
    s = normalize_label(raw)
    if not s:
        return []
    if _is_noise(s, noise):
        return [s]
    out = []
    if ":" in s:
        prefix, _, value = s.partition(":")
        prefix, value = prefix.strip(), value.strip()
        if value in _NEGATIVE_VALUES:
            return []
        if value in _POSITIVE_VALUES:
            return [prefix]
        parts = [value]
    else:
        parts = [s]
    for part in parts:
        for tag in _COMMA_SPLIT_RE.split(part):
            tag = normalize_label(tag)
            if tag:
                out.append(tag)
    return out


def _match_concept(tag: str, cat: dict):
    cid = cat["aliases"].get(tag)
    if cid:
        return cid
    # fallback: najdłuższy alias występujący jako całe słowo/fraza (min. 5 znaków)
    return next((acid for rx, acid in cat["phrases"] if rx.search(tag)), None)


def canonicalize(labels) -> dict:
    """labels: iterable surowych etykiet -> {'canonical': [id...], 'unmatched': [str...], 'noise': [str...]}.

    'canonical' w kolejności katalogu (stabilnie), 'unmatched'/'noise' bez duplikatów (case-insensitive).
    """
    cat = load_catalog()
    found, unmatched, noise_out = set(), {}, {}
    for raw in labels or []:
        for tag in split_label(raw, cat["noise"]):
            if _is_noise(tag, cat["noise"]):
                noise_out.setdefault(tag, tag)
                continue
            cid = _match_concept(tag, cat)
            if cid:
                found.add(cid)
            else:
                unmatched.setdefault(tag, tag)
    canonical = sorted(found, key=lambda c: cat["order"].get(c, 10**6))
    return {"canonical": canonical, "unmatched": sorted(unmatched), "noise": sorted(noise_out)}


def build_amenities(labels, raw_codes=None, extra_canonical=None, extra_unmatched=None) -> dict:
    """Składa kompletny blok `amenities` rekordu z surowych etykiet (oraz opcjonalnie już-kanonicznych)."""
    res = canonicalize(labels)
    cat = load_catalog()
    canonical = sorted(
        (c for c in {*res["canonical"], *(extra_canonical or [])} if c in cat["concepts"]),
        key=cat["order"].__getitem__,
    )
    unmatched = {u.lower(): u for u in [*res["unmatched"], *(extra_unmatched or [])]}
    unmatched = sorted(unmatched.values())
    return {
        "labels": [cat["concepts"][c]["label"] for c in canonical] + unmatched,
        "raw_codes": list(raw_codes or []),
        "canonical": canonical,
        "unmatched": unmatched,
    }
