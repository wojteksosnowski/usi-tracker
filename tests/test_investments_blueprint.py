import pytest
from flask import Flask
from python_worker.api.blueprints.investments import investments_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(investments_bp, url_prefix="/api")
    return app

@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    return app.test_client()

def test_register_bulk_missing_payload(client):
    response = client.post("/api/register-bulk", json={"portal": "otodom"})
    assert response.status_code == 400
    assert "Missing investments list" in response.get_json()["error"]

def test_register_bulk_invalid_portal(client):
    response = client.post("/api/register-bulk", json={"portal": "unknown", "investments": [{"url": "abc"}]})
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_register_bulk_success(client, monkeypatch):
    from python_worker.api.blueprints.investments import job_manager
    from python_worker.services.scraper_gateway import ScraperGateway

    # Mock normalize_portal_name to ensure it passes
    monkeypatch.setattr(ScraperGateway, "normalize_portal_name", lambda p: "oto")

    started_jobs = []
    def mock_start_job(name, func, *args):
        started_jobs.append({"name": name, "args": args})
        return "job-bulk-123"

    monkeypatch.setattr(job_manager, "start_job", mock_start_job)

    response = client.post("/api/register-bulk", json={
        "portal": "otodom",
        "investments": [{"url": "https://otodom.pl/test-inv"}]
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["job_id"] == "job-bulk-123"
    assert len(started_jobs) == 1
    assert "Bulk Register: OTO" in started_jobs[0]["name"]

def test_register_single_success(client, monkeypatch):
    from python_worker.api.blueprints.investments import investment_service
    
    def mock_register_investment(portal=None, payload=None):
        return {"ok": True, "job_id": "job-reg-123"}
        
    monkeypatch.setattr(investment_service, "register_investment", mock_register_investment)
    
    response = client.post("/api/register", json={
        "portal": "otodom",
        "url": "https://otodom.pl/inv"
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["job_id"] == "job-reg-123"

def test_register_single_bad_request(client, monkeypatch):
    from python_worker.api.blueprints.investments import investment_service
    
    def mock_register_investment(portal=None, payload=None):
        raise ValueError("Invalid portal")
        
    monkeypatch.setattr(investment_service, "register_investment", mock_register_investment)
    
    response = client.post("/api/register", json={"portal": "invalid"})
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_get_image_placeholder_when_missing(client):
    response = client.get("/api/image/non_existent_folder/missing.jpg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.content_type
