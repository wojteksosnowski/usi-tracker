"""Raport lokalizacji w PDF: poprawne kodowanie polskich znaków i osadzony font."""
import re
from datetime import datetime

from python_worker.pdf.location_report_pdf import (
    _overall_view, _star_row, fmt_num, render_location_report_html, render_location_report_pdf)

PL = "ĄĆĘŁŃÓŚŹŻ ąćęłńóśźż"

REPORT = {
    "center": {"lat": 51.1, "lon": 17.03, "label": "Wrocław, ul. Świdnicka"},
    "limit": 12, "area_km": 2.5, "years": [2026], "total": 2, "count": 2,
    "data": [
        {"name": "Żoliborz Łąkowa", "developer": "Śląski Dom", "district": "Śródmieście",
         "delivery": "III kw. 2026", "distance": 0.8, "price_m2_min": 14250, "price_m2_max": 16000, "status": "w sprzedaży",
         "ratings": {"Balkony": 3, "Fasady": 4, "Wnętrza": 2, "Teren": 3, "Mieszkania": 3, "Udogodnienia": 1}},
        {"name": "Gdańsk Zdrój", "developer": "Źródło", "district": "Wrzeszcz",
         "delivery": None, "distance": 1.2, "price_m2_min": None, "status": "w budowie"},
    ],
}


def test_fmt_num_polish_convention():
    assert fmt_num(12540.3, 1) == "12 540,3"


def test_html_keeps_polish_characters():
    html = render_location_report_html(REPORT, now=datetime(2026, 10, 5))
    for text in ("Wrocław", "Świdnicka", "Żoliborz Łąkowa", "Śląski Dom · III kw. 2026", "5 października 2026",
                 "Inwestowanie wiąże się z ryzykiem"):
        assert text in html


def test_cover_table_and_cards_structure():
    html = render_location_report_html(REPORT, now=datetime(2026, 10, 5))
    assert "System monitoringu rynku" not in html
    assert html.index('class="cover"') < html.index('class="inner"') < html.index('class="cards"')
    assert "Karty inwestycji" in html and 'class="cards-title"' not in html
    for gone in ("Dzielnica", "Odległość", "<th>Status</th>", "g-spectrum", 'class="edge"'):
        assert gone not in html
    assert "Cena m² do" in html and "16\u00a0000" in html
    for cat in ("Balkony", "Fasady", "Wnętrza", "Teren", "Mieszkania", "Udogodnienia"):
        assert cat in html
    assert html.count('class="card"') == 2
    card = html.split('class="card"')[1]
    assert card.index('class="photo') < card.index('class="nm"') < card.index('class="dev"') < card.index('class="grid"')
    assert card.count('class="r"') == 6


def test_pdf_embeds_signika_and_is_valid():
    pdf = render_location_report_pdf(REPORT, sort={"key": "distance", "dir": "asc"}, uncompressed_pdf=True)
    assert pdf.startswith(b"%PDF")
    assert re.search(rb"/FontName /[A-Z]{6}\+Signika", pdf)


def test_pdf_without_rows():
    pdf = render_location_report_pdf({**REPORT, "count": 0, "data": [], "area_km": None})
    assert pdf.startswith(b"%PDF")


def test_endpoint_returns_pdf_and_errors(monkeypatch):
    from flask import Flask
    from python_worker.api.blueprints import reports

    app = Flask(__name__)
    app.register_blueprint(reports.reports_bp, url_prefix="/api")
    client = app.test_client()

    monkeypatch.setattr(reports, "_build_location_report", lambda body: REPORT)
    r = client.post("/api/reports/location/pdf", json={"location": "x"})
    assert r.status_code == 200 and r.mimetype == "application/pdf" and r.data.startswith(b"%PDF")
    assert "raport-lokalizacji.pdf" in r.headers["Content-Disposition"]

    def boom(body):
        raise reports._ReportError("Nie rozpoznano lokalizacji", 422)
    monkeypatch.setattr(reports, "_build_location_report", boom)
    r = client.post("/api/reports/location/pdf", json={})
    assert r.status_code == 422 and "lokalizacji" in r.get_json()["error"]


def test_card_thumbnail_embedded_when_photo_exists(tmp_path, monkeypatch):
    from PIL import Image
    from python_worker import config
    (tmp_path / "dev" / "inv").mkdir(parents=True)
    Image.new("RGB", (600, 400), "red").save(tmp_path / "dev" / "inv" / "a.jpg")
    monkeypatch.setattr(config, "PUBLIC_USI_DIR", tmp_path)
    data = [{**REPORT["data"][0], "photos": ["/api/image/dev/inv/a.jpg"]}, REPORT["data"][1]]
    html = render_location_report_html({**REPORT, "data": data}, now=datetime(2026, 10, 5))
    assert html.count('<img class="photo"') == 1 and "data:image/jpeg;base64," in html


def test_card_shows_overall_stars_without_status_or_number():
    html = render_location_report_html(REPORT, now=datetime(2026, 10, 5))
    assert html.count('class="ov"') == 1  # tylko inwestycja z ocenami
    assert not re.search(r"\d,\d\d", html.split("Karty inwestycji")[1].split("</section>")[0].replace("14\u00a0250", ""))
    assert "w sprzedaży" not in html and "w budowie" not in html and 'class="tag' not in html


def test_delivery_filter_applies_before_limit(monkeypatch):
    from python_worker.api.blueprints import reports

    area = [{"name": f"I{i}", "distance": float(i), "delivery": "2026" if i % 2 else "2028"}
            for i in range(1, 11)]

    class Idx:
        def get_near_coordinates(self, lat, lon, km, limit=24):
            return area[:limit]
    monkeypatch.setattr(reports.inv_index, "get_investment_index", lambda: Idx())
    monkeypatch.setattr(reports, "HereMapsService", lambda key: type("H", (), {"geocode_address": None})())
    monkeypatch.setattr(reports, "parse_gmaps_location", lambda loc, geocoder=None: {"lat": 1, "lon": 1})

    r = reports._build_location_report({"location": "x", "limit": 3, "delivery": ["2028"]})
    assert r["count"] == 3 and r["total"] == 5
    assert [i["name"] for i in r["data"]] == ["I2", "I4", "I6"]
    assert r["years"] == [2026, 2028]


def test_star_row_rounds_to_half_and_stars_are_monochrome():
    import base64
    from python_worker.pdf.location_report_pdf import _star_row, star_uri, zero_uri
    full, half, empty = star_uri("full"), star_uri("half"), star_uri("empty")
    zero_on, zero_off = zero_uri(True), zero_uri(False)
    assert _star_row(2.5) == [zero_off, full, full, half, empty]
    assert _star_row(3.9) == [zero_off] + [full] * 4
    assert _star_row(0) == [zero_on] + [empty] * 4
    svg = base64.b64decode(half.split(",")[1]).decode()
    assert "clip-path" in svg and 'fill-opacity=".22"' in svg
    assert 'fill="#000"' in svg


def test_cover_uses_dusk_gradient_and_fine_noise():
    from PIL import Image
    css = open("python_worker/pdf/location_report.css", encoding="utf-8").read()
    assert "assets/noise.png" in css and "linear-gradient(120deg, var(--blue) 0%, var(--magenta) 100%)" in css
    with Image.open("python_worker/pdf/assets/noise.png") as im:
        assert im.size[0] >= 1024 and im.mode == "LA" and im.getextrema()[1][1] <= 40  # delikatny: alfa ≤ ~15%


def test_pdf_has_cover_table_and_card_pages_and_serif_font_files():
    from pathlib import Path
    rep = {**REPORT, "data": REPORT["data"] * 4, "count": 8}
    pdf = render_location_report_pdf(rep, uncompressed_pdf=True)
    assert len(re.findall(rb"/Type /Page\b", pdf)) >= 3
    css = Path("python_worker/pdf/location_report.css").read_text(encoding="utf-8")
    for face in ("Regular", "It", "Semibold"):  # na macOS Pango ignoruje @font-face — pliki muszą być w repo dla serwera
        assert f"fonts/SourceSerif4-{face}.ttf" in css and Path(f"python_worker/pdf/fonts/SourceSerif4-{face}.ttf").is_file()


def test_footer_uses_warstadt_domain_not_usi_pl():
    from pathlib import Path
    html = render_location_report_html(REPORT, now=datetime(2026, 10, 5))
    css = Path("python_worker/pdf/location_report.css").read_text(encoding="utf-8")
    assert html.count("war<strong>stadt</strong>.com") == 2  # strona tabeli + karty
    assert "usi.pl" not in html and "usi.pl" not in css
    assert css.count("element(foot)") == 2
    assert Path("python_worker/pdf/assets/usi-star-color.svg").is_file()


def test_star_row_has_zero_icon_plus_four_stars():
    assert len(_star_row(3)) == 5
    assert _star_row(0)[0] != _star_row(3)[0]  # zero pełne tylko dla oceny 0
    assert _star_row(2)[0] == _star_row(4)[0]


def test_overall_view_fractions():
    assert _overall_view(0.75)["frac"] == "¾" and len(_overall_view(0.75)["icons"]) == 1
    assert _overall_view(2.25)["frac"] == "¼" and len(_overall_view(2.25)["icons"]) == 2
    assert _overall_view(3)["frac"] == ""


def test_card_description_optional():
    data = [{**REPORT["data"][0], "description": "Opis osiedla"}, REPORT["data"][1]]
    html = render_location_report_html({**REPORT, "data": data}, now=datetime(2026, 10, 5))
    assert html.count('class="txt"') == 1 and "Opis osiedla" in html


def test_missing_category_rating_is_greyed_out():
    from python_worker.pdf.location_report_pdf import zero_uri
    ratings = {"Balkony": 0, "Fasady": 3, "Wnętrza": 2, "Teren": None, "Mieszkania": 3, "Udogodnienia": 1}
    data = [{**REPORT["data"][0], "ratings": ratings}]
    html = render_location_report_html({**REPORT, "data": data, "count": 1}, now=datetime(2026, 10, 5))
    card = html.split('class="card"')[1]
    assert card.count('class="r na"') == 1 and card.count('class="r"') == 5
    assert card.index("Teren") > card.index('class="r na"')
    assert zero_uri(True) in card  # ocena 0 (Balkony) zostaje pełna
