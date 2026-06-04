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
