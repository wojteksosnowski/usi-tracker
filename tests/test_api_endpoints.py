import pytest
from flask import Flask
from python_worker.ui_server import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_api_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.is_json

def test_api_metadata_config(client):
    response = client.get("/api/metadata-config")
    assert response.status_code == 200
    assert response.is_json

def test_api_investments_list(client):
    response = client.get("/api/investments")
    assert response.status_code == 200
    assert response.is_json

def test_api_developers_list(client):
    response = client.get("/api/developers")
    assert response.status_code == 200
    assert response.is_json

def test_static_index(client):
    response = client.get("/")
    assert response.status_code in [200, 404]  # 404 is fine if ui/index.html is missing in tests

def test_refresh_developer_route_starts_job(client, monkeypatch):
    # Mocking dependencies
    from python_worker.api.blueprints.investments import developer_manager, job_manager

    # Mock get_developer_by_id
    monkeypatch.setattr(developer_manager, "get_developer_by_id", 
                        lambda usi_dev_id: {"usi_dev_id": usi_dev_id, "name": "Test Dev", "developer_slug": "test-dev"})

    # Track calls to start_job
    started_jobs = []
    def mock_start_job(name, func, *args):
        started_jobs.append({"name": name, "args": args})
        return "job-123"

    monkeypatch.setattr(job_manager, "start_job", mock_start_job)

    response = client.post("/api/developer/DEV-00001/refresh")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["job_id"] == "job-123"

    # Verify that start_job was called correctly
    assert len(started_jobs) == 1
    assert "Refresh Deweloper: Test Dev" in started_jobs[0]["name"]
    assert started_jobs[0]["args"][0] == "DEV-00001"

