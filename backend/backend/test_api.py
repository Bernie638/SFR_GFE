# backend/test_api.py
import os
from dotenv import load_dotenv
import pytest

# 1) load your .env  
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 2) import your Flask app instance  
from quiz_app_backend import app  # or whatever your app object is named

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_env_loaded():
    # sanity check that our .env values came through
    assert os.getenv("DB_PATH") is not None
    assert os.getenv("IMAGES_DIR") is not None

def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "ok"

def test_topics_endpoint(client):
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)  # or dict, depending

def test_stats_endpoint(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert "totalQuestions" in resp.get_json()
