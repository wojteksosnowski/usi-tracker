"""Raport lokalizacji w PDF — HTML/CSS (design system USI) renderowany WeasyPrint.

Polskie znaki: szablon jest UTF-8, a font Signika (TTF z design systemu) osadzany w PDF.
"""
import base64
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

RATING_MAX = 4  # skala ocen kategorii (por. _STANDARD_TIERS w amenity_scorer)

PDF_DIR = Path(__file__).resolve().parent
_env = Environment(loader=FileSystemLoader(PDF_DIR), autoescape=select_autoescape(["html"]))

_MONTHS = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
           "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]

SORT_KEYS = {"name", "developer", "district", "delivery", "distance", "price_m2_min", "price_m2_max"}
THUMB_PX = 620  # bok kwadratowej miniatury w PDF: 52,5 mm przy 300 dpi


_STAR_VIEWBOX = (6238, 1045, 1400, 1340)  # jak w assets/usi-star-black.svg


@lru_cache(maxsize=None)
def star_uri(kind):
    """Data-URI czarnej gwiazdki USI: "full", "empty" (krycie .22) lub "half" (lewa połowa pełna).

    Odpowiada `i`, `i.e`, `i.h` z ui_kits/print/InvestmentCards.html.
    """
    svg = (PDF_DIR / "assets" / "usi-star-black.svg").read_text(encoding="utf-8")
    path = re.search(r'<path[^>]*/>', svg).group(0)
    dim = path.replace('fill="#000"', 'fill="#000" fill-opacity=".22"')
    x, y, w, h = _STAR_VIEWBOX
    body = {"full": path, "empty": dim,
            "half": f'<clipPath id="h"><rect x="{x}" y="{y}" width="{w / 2}" height="{h}"/></clipPath>'
                    f'{dim}<g clip-path="url(#h)">{path}</g>'}[kind]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}">{body}</svg>'
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


@lru_cache(maxsize=None)
def zero_uri(full):
    """Data-URI ikony „zero" (usi-zero-black.svg); `full=False` → przygaszona (.22) jak `i.z.e` w designie."""
    svg = (PDF_DIR / "assets" / "usi-zero-black.svg").read_text(encoding="utf-8")
    if not full:
        svg = svg.replace("<svg ", '<svg opacity=".22" ', 1)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def fmt_num(value, decimals=0):
    """Polska konwencja: spacja (nbsp) jako separator tysięcy, przecinek dziesiętny."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def fmt_pln(value):
    return f"{fmt_num(round(value))} PLN" if value else "—"


def fmt_date(dt):
    return f"{dt.day} {_MONTHS[dt.month - 1]} {dt.year}"


def _star_row(score):
    """Ikona „zero" + RATING_MAX gwiazdek jako data-URI (jak `i.z` + `i` w designie kart).

    Zero jest pełne tylko dla oceny 0; gwiazdki zaokrąglone do połówki (i.h).
    """
    score = max(0, min(score or 0, RATING_MAX))
    halves = round(score * 2)
    kinds = ["full" if halves >= 2 * (i + 1) else "half" if halves == 2 * i + 1 else "empty"
             for i in range(RATING_MAX)]
    return [zero_uri(halves == 0)] + [star_uri(k) for k in kinds]


_FRACTIONS = {0: "", 1: "¼", 2: "½", 3: "¾"}


def _overall_view(score):
    """Ocena ogólna jak `.ov` w designie: pełne gwiazdki (lub „zero" poniżej 1) + ułamek ¼/½/¾."""
    quarters = round(max(0, min(score, RATING_MAX)) * 4)
    full, frac = divmod(quarters, 4)
    icons = [star_uri("full")] * full if full else [zero_uri(True)]
    return {"icons": icons, "frac": _FRACTIONS[frac]}


def _ratings_view(ratings):
    from python_worker.api.utils import CATS
    from python_worker.services.amenity_scorer import calculate_ocena_log
    ratings = ratings or {}
    cats = [{"key": k, "stars": _star_row(round(ratings[k])), "missing": False} if ratings.get(k) is not None
            else {"key": k, "stars": [zero_uri(False)] + [star_uri("empty")] * RATING_MAX, "missing": True}
            for k in CATS]
    overall = calculate_ocena_log(ratings)
    return {"ratings": cats, "has_ratings": overall is not None,
            "overall": _overall_view(overall) if overall is not None else None}


def _short_description(text, limit=300):
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def _thumb_uri(photos):
    """Data-URI (JPEG, zmniejszony) pierwszego dostępnego zdjęcia z PUBLIC_USI_DIR; brak → None."""
    import base64
    import io
    from urllib.parse import unquote
    from python_worker.config import PUBLIC_USI_DIR
    root = Path(PUBLIC_USI_DIR).resolve()
    for photo in photos or []:
        if isinstance(photo, dict):
            photo = (photo.get("thumbnail") or photo.get("medium") or photo.get("small")
                     or photo.get("large") or photo.get("url"))
        if not isinstance(photo, str) or photo.startswith(("http://", "https://")):
            continue
        rel = unquote(photo).split("/api/image/")[-1].split("Public/USI/")[-1].lstrip("/")
        path = (root / rel).resolve()
        if root not in path.parents or not path.is_file():
            continue
        try:
            from PIL import Image, ImageOps
            with Image.open(path) as im:
                im = ImageOps.fit(im.convert("RGB"), (THUMB_PX, THUMB_PX))
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=80)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        except Exception:
            continue
    return None


def _sorted(data, sort):
    key = (sort or {}).get("key")
    if key not in SORT_KEYS:
        return list(data)
    rev = (sort or {}).get("dir") == "desc"
    present = [d for d in data if d.get(key) not in (None, "")]
    missing = [d for d in data if d.get(key) in (None, "")]
    return sorted(present, key=lambda d: d[key], reverse=rev) + missing


def render_location_report_html(report, sort=None, delivery_label=None, now=None):
    now = now or datetime.now()
    center = report["center"]
    place = center.get("label") or f"{center['lat']:.5f}, {center['lon']:.5f}"
    area_km = report.get("area_km")
    rows = _sorted(report["data"], sort)
    prices = [r["price_m2_min"] for r in rows if r.get("price_m2_min")]
    view = [{
        "name": r.get("name") or "—",
        "developer": r.get("developer") or "",
        "district": r.get("district") or "—",
        "delivery": r.get("delivery") or "—",
        "distance": f"{fmt_num(r['distance'], 1)} km" if r.get("distance") is not None else "—",
        "price_m2": fmt_pln(r.get("price_m2_min")),
        "price_m2_max": fmt_pln(r.get("price_m2_max")),
        "thumb": _thumb_uri(r.get("photos")),
        "description": _short_description(r.get("description")),
        **_ratings_view(r.get("ratings")),
    } for r in rows]
    area_txt = f" w zasięgu {fmt_num(area_km, 1)} km" if area_km is not None else ""
    return _env.get_template("location_report.html").render(
        generated=fmt_date(now),
        lede=f"Pokazano {report['count']} z {report['total']} inwestycji{area_txt} od: {place}.",
        count=report["count"],
        area_km=f"{fmt_num(area_km, 1)} km" if area_km is not None else "—",
        avg_m2=fmt_pln(sum(prices) / len(prices)) if prices else "—",
        filter_label=delivery_label or "dowolny",
        rows=view,
    )


def render_location_report_pdf(report, sort=None, delivery_label=None, now=None, **pdf_options):
    from weasyprint import HTML, CSS  # import leniwy: brak pango nie psuje reszty API
    html = render_location_report_html(report, sort, delivery_label, now)
    return HTML(string=html, base_url=str(PDF_DIR)).write_pdf(
        stylesheets=[CSS(filename=str(PDF_DIR / "location_report.css"))], **pdf_options)
