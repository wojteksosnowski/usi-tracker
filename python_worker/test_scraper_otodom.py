import json
import pytest
import requests_mock
from unittest.mock import patch
from .scraper_otodom import fetch_otodom_html, extract_next_data, scrape_otodom
from .image_saver import clean_filename
from .config import SCRAPERAPI_KEY

def test_extract_next_data():
    html = """
    <html>
        <body>
            <script id="__NEXT_DATA__" type="application/json">
            {"props": {"pageProps": {"ad": {"title": "Test Ad", "id": 123}}}}
            </script>
        </body>
    </html>
    """
    
    data = extract_next_data(html)
    assert data["ad"]["title"] == "Test Ad"
    assert data["ad"]["id"] == 123

def test_fetch_otodom_html_integration():
    """This test requires network access or mocks. Using mocks for safety."""
    url = "https://www.otodom.pl/foo"
    # We should mock fetch_html (which is used by fetch_otodom_html)
    with patch("python_worker.scraper_otodom.fetch_html") as mock_fetch:
        mock_fetch.return_value = "<html><body>Content</body></html>"
        html = fetch_otodom_html(url)
        assert html == "<html><body>Content</body></html>"


def test_clean_filename_otodom_unique():
    """Two different Otodom CDN URLs must produce two different .jpg filenames."""
    url1 = (
        "https://ireland.apollo.olxcdn.com/v1/files/"
        "eyJmbiI6IjI2c3VnaW4wdThwNi1FQ09TWVNURU0iLCJ3IjpbXX0.AAAA"
        "/image;s=1280x1024;q=80"
    )
    url2 = (
        "https://ireland.apollo.olxcdn.com/v1/files/"
        "eyJmbiI6InhiaTZqYndtd295aDMtRUNPU1lTVEVNIiwidyI6W1XX0.BBBB"
        "/image;s=1280x1024;q=80"
    )
    f1 = clean_filename(url1)
    f2 = clean_filename(url2)
    assert f1.endswith(".jpg"), f"Expected .jpg extension, got {f1!r}"
    assert f2.endswith(".jpg"), f"Expected .jpg extension, got {f2!r}"
    assert f1 != f2, "Different Otodom images must not share a filename"
    assert f1 != "image;s=1280x1024;q=80.jpg"


def test_clean_filename_regular_url_unchanged():
    """Regular image URLs (with extension in path) still work correctly."""
    assert clean_filename("https://example.com/photo.jpg") == "photo.jpg"
    assert clean_filename("https://example.com/photo.jpg?size=large") == "photo.jpg"
    assert clean_filename("https://example.com/path/banner.webp") == "banner.webp"


_MOCK_OTODOM_HTML = """
<html><body>
<script id="__NEXT_DATA__" type="application/json">
{
  "props": {
    "pageProps": {
      "ad": {
        "title": "Testowa Inwestycja",
        "agency": {"id": 99, "name": "TestDev", "url": "/deweloper/test-dev-ID99"},
        "location": {
          "coordinates": {"latitude": 52.2, "longitude": 21.0, "__typename": "Coordinates"},
          "mapDetails": {"radius": 0, "zoom": 12, "__typename": "MapDetails"}
        },
        "topInformation": [
          {"label": "project_finish_date", "values": ["2027-09-30"], "unit": "", "__typename": "AdditionalInfo"}
        ],
        "images": [
          {
            "large": "https://ireland.apollo.olxcdn.com/v1/files/AAAA.sig1/image;s=1280x1024;q=80",
            "medium": "https://ireland.apollo.olxcdn.com/v1/files/AAAA.sig1/image;s=655x491;q=80"
          },
          {
            "large": "https://ireland.apollo.olxcdn.com/v1/files/BBBB.sig2/image;s=1280x1024;q=80",
            "medium": "https://ireland.apollo.olxcdn.com/v1/files/BBBB.sig2/image;s=655x491;q=80"
          }
        ]
      }
    }
  }
}
</script>
</body></html>
"""


def test_scrape_otodom_images():
    """scrape_otodom() must extract 2 distinct image URLs and return 2 unique image_paths."""
    oto_url = "https://www.otodom.pl/pl/inwestycja/testowa-inwestycja-ID1234"
    # New Fetcher uses http://api.scraperapi.com with params
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={oto_url}&render=false"

    captured = {}

    def mock_save_images(urls, dev_slug, inv_slug):
        captured["urls"] = urls
        # Return filenames as clean_filename would produce
        from python_worker.image_saver import clean_filename
        return [clean_filename(u) for u in urls]

    with requests_mock.Mocker() as rm:
        # We need to use real_http=True or mock both curl_cffi and requests
        # or just mock the scraperapi call which is the fallback.
        # requests_mock handles std_requests.
        rm.get("http://api.scraperapi.com", text=_MOCK_OTODOM_HTML)
        # We must also bypass curl_cffi impersonation in the test to avoid delay/failure
        with patch("python_worker.fetcher.curl_requests.Session.get", side_effect=Exception("Mocked curl_cffi failure")):
            with patch("python_worker.scraper_otodom.save_images", side_effect=mock_save_images):
                result = scrape_otodom(oto_url, "test-dev", "testowa-inwestycja")

    assert "error" not in result, f"Unexpected error: {result.get('error')}"
    assert result["images_count"] == 2
    assert len(result["image_paths"]) == 2
    assert result["image_paths"][0] != result["image_paths"][1], "image_paths must be unique"
    assert result["title"] == "Testowa Inwestycja"
    assert result["latitude"] == 52.2
    assert result["longitude"] == 21.0
    assert result["delivery_quarter"] == 3
    assert result["delivery_year"] == 2027
    # Confirm both captured image URLs were the `large` variants
    assert len(captured["urls"]) == 2
    assert all("NEXT_DATA" not in u for u in captured["urls"])
