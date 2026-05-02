"""Tests for ui_server validation helpers and image-serving endpoint."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from python_worker.ui_server import _valid_filename, _valid_slug, app


# ── _valid_filename ────────────────────────────────────────────────────────────

class TestValidFilename:
    def test_empty_string(self):
        assert _valid_filename("") is False

    def test_rp_style_webp(self):
        assert _valid_filename("wizualizacje-mieszkanie-1.webp") is True

    def test_rp_style_jpg(self):
        assert _valid_filename("photo-01.jpg") is True

    def test_otodom_jwt_filename(self):
        # Otodom CDN format: base64url.jwt-token.jpg (two dots in stem)
        assert _valid_filename("eyJmb.yc31izt-d83q.jpg") is True

    def test_otodom_real_filename(self):
        fname = (
            "eyJmbiI6InBldnN5eGR0amJiNzMtRUNPU1lTVEVNIiwidyI6W3siZm4iOiJlbnZmcXFlMWF5NGsxLUFQTCIsInMiOiIxNCIsInAiOiIxMCwtMTAiLCJhIjoiMCJ9XX0"
            ".yc31izt-d83qV-YLCG8Q1NXR6AQc5wD4M9n6SHlcC4w"
            ".jpg"
        )
        assert _valid_filename(fname) is True

    def test_path_traversal_dotdot(self):
        assert _valid_filename("../etc/passwd.jpg") is False

    def test_double_dot_in_stem(self):
        assert _valid_filename("foo..bar.jpg") is False

    def test_no_extension(self):
        assert _valid_filename("noextension") is False

    def test_unknown_extension(self):
        assert _valid_filename("photo.gif") is False

    def test_slash_in_filename(self):
        assert _valid_filename("a/b.jpg") is False

    def test_jpeg_extension(self):
        assert _valid_filename("image.jpeg") is True

    def test_png_extension(self):
        assert _valid_filename("image.png") is True

    def test_svg_extension(self):
        assert _valid_filename("icon.svg") is True

    def test_case_insensitive_extension(self):
        assert _valid_filename("photo.JPG") is True

    def test_dot_only_stem(self):
        assert _valid_filename(".jpg") is False

    def test_multiple_segments(self):
        # three segments before extension — also valid
        assert _valid_filename("a.b.c.jpg") is True


# ── _valid_slug ────────────────────────────────────────────────────────────────

class TestValidSlug:
    def test_normal_slug(self):
        assert _valid_slug("green-house-development") is True

    def test_underscore_slug(self):
        assert _valid_slug("my_investment") is True

    def test_alphanumeric(self):
        assert _valid_slug("inv123") is True

    def test_slug_with_space(self):
        assert _valid_slug("green house") is False

    def test_slug_with_dot(self):
        assert _valid_slug("dev.corp") is False

    def test_empty_slug(self):
        assert _valid_slug("") is False

    def test_slug_with_slash(self):
        assert _valid_slug("foo/bar") is False


# ── Flask integration: /api/image/ endpoint ────────────────────────────────────

@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestServeImage:
    def test_rp_filename_returns_200(self, client, tmp_path):
        img_dir = tmp_path / "dev" / "inv"
        img_dir.mkdir(parents=True)
        (img_dir / "photo-01.jpg").write_bytes(b"\xff\xd8\xff")

        with patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path)):
            resp = client.get("/api/image/dev/inv/photo-01.jpg")
            assert resp.status_code == 200

    def test_otodom_jwt_filename_returns_200_not_400(self, client, tmp_path):
        img_dir = tmp_path / "dev" / "inv"
        img_dir.mkdir(parents=True)
        fname = "eyJmb.yc31izt-d83q.jpg"
        (img_dir / fname).write_bytes(b"\xff\xd8\xff")

        with patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path)):
            resp = client.get(f"/api/image/dev/inv/{fname}")
            # Should NOT be 400 (validation failure) — 200 or 404 are both acceptable
            assert resp.status_code != 400

    def test_invalid_slug_returns_400(self, client):
        resp = client.get("/api/image/bad slug!/inv/photo.jpg")
        # Flask won't even route this — likely 404 from routing, not 400, but definitely not 200
        assert resp.status_code in (400, 404)

    def test_missing_file_returns_404(self, client, tmp_path):
        with patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path)):
            resp = client.get("/api/image/dev/inv/nonexistent.jpg")
            assert resp.status_code == 404

    def test_unknown_extension_returns_400(self, client):
        resp = client.get("/api/image/dev/inv/photo.gif")
        assert resp.status_code == 400


# ── Metadata Config ────────────────────────────────────────────────────────────

class TestMetadataConfig:
    def test_metadata_config_returns_json(self, client):
        resp = client.get("/api/metadata-config")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert any(d["key"] == "address" for d in data)


# ── Shared fixture helpers ─────────────────────────────────────────────────────

def _make_inv_dir(tmp_path, dev="dev", inv="inv"):
    """Create minimal USIdata/{dev}/{inv}/usi_{inv}.json."""
    inv_dir = tmp_path / dev / inv
    inv_dir.mkdir(parents=True)
    (inv_dir / f"usi_{inv}.json").write_text(json.dumps({
        "investment_slug": inv,
        "developer_slug": dev,
        "name": "Test Investment",
        "location": {"coords": [54.0, 18.0]},
        "specifications": {"units_count": 0, "delivery_date": "—"},
        "financials": {"price_avg": 0},
        "amenities": {"labels": [], "raw_codes": []},
        "ratings": {},
        "status": "Brak"
    }))
    return inv_dir


# ── /api/ratings/<dev>/<inv> ───────────────────────────────────────────────────

class TestSaveRatings:
    def test_save_ratings_returns_ok(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            resp = client.post("/api/ratings/dev/inv",
                               json={"Balkony": 3, "Fasady": 2, "komentarz": "", "status": "Brak"})
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_save_ratings_persists_to_file(self, client, tmp_path):
        inv_dir = _make_inv_dir(tmp_path)
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            client.post("/api/ratings/dev/inv",
                        json={"Balkony": 4, "Fasady": 1, "komentarz": "ok", "status": "Wstępna"})
        saved = json.loads((inv_dir / "meta_inv_ratings.json").read_text())
        assert saved["Balkony"] == 4
        assert saved["Fasady"] == 1
        assert saved["komentarz"] == "ok"
        assert saved["status"] == "Wstępna"

    def test_ratings_visible_in_investment_data(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            client.post("/api/ratings/dev/inv",
                        json={"Balkony": 3, "Wnętrza": 2, "komentarz": "test", "status": "AI"})
            resp = client.get("/api/data/dev/inv")
        data = resp.get_json()
        assert data["ratings"]["Balkony"] == 3
        assert data["ratings"]["Wnętrza"] == 2
        assert data["comment"] == "test"
        assert data["status"] == "AI"

    def test_ratings_visible_in_investments_list(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            client.post("/api/ratings/dev/inv",
                        json={"Fasady": 4, "komentarz": "", "status": "Pełna"})
            resp = client.get("/api/investments")
        investments = resp.get_json()
        found = next((i for i in investments if i["slug"] == "dev/inv"), None)
        assert found is not None
        assert found["ratings"]["Fasady"] == 4
        assert found["status"] == "Pełna"

    def test_save_ratings_invalid_value_returns_400(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            resp = client.post("/api/ratings/dev/inv",
                               json={"Balkony": 5, "status": "Brak", "komentarz": ""})
        assert resp.status_code == 400

    def test_save_ratings_invalid_status_returns_400(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            resp = client.post("/api/ratings/dev/inv",
                               json={"status": "Nieznany", "komentarz": ""})
        assert resp.status_code == 400

    def test_save_ratings_missing_investment_returns_404(self, client, tmp_path):
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            resp = client.post("/api/ratings/dev/nonexistent",
                               json={"status": "Brak", "komentarz": ""})
        assert resp.status_code == 404


# ── /api/mark-delete/<dev>/<inv> ──────────────────────────────────────────────

class TestMarkDelete:
    def test_mark_delete_returns_ok_and_count(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        paths = ["/api/image/dev/inv/a.jpg", "/api/image/dev/inv/b.jpg"]
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            resp = client.post("/api/mark-delete/dev/inv", json={"paths": paths})
        body = resp.get_json()
        assert resp.status_code == 200
        assert body["ok"] is True
        assert body["count"] == 2

    def test_mark_delete_creates_deletion_list(self, client, tmp_path):
        inv_dir = _make_inv_dir(tmp_path)
        paths = ["/api/image/dev/inv/photo.jpg"]
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            client.post("/api/mark-delete/dev/inv", json={"paths": paths})
        saved = json.loads((inv_dir / "deletion_list.json").read_text())
        assert saved["paths"] == paths
        assert "updated_at" in saved

    def test_photos_to_delete_count_in_investment_data(self, client, tmp_path):
        _make_inv_dir(tmp_path)
        paths = ["/api/image/dev/inv/a.jpg", "/api/image/dev/inv/b.jpg"]
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            client.post("/api/mark-delete/dev/inv", json={"paths": paths})
            resp = client.get("/api/data/dev/inv")
        assert resp.get_json()["photos_to_delete"] == 2

    def test_mark_delete_missing_investment_returns_404(self, client, tmp_path):
        with patch("python_worker.ui_server.USI_DATA_DIR", str(tmp_path)), \
             patch("python_worker.ui_server.PUBLIC_USI_DIR", str(tmp_path / "usi")):
            resp = client.post("/api/mark-delete/dev/nonexistent", json={"paths": []})
        assert resp.status_code == 404

    def test_mark_delete_invalid_slug_returns_400(self, client):
        resp = client.post("/api/mark-delete/dev.corp/inv", json={"paths": []})
        assert resp.status_code == 400
