"""
Tests for NeuroTrace Flask Application and REST API.
"""
import pytest
from flask_app import app, SESSION_STORE


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_flask_status_endpoint(client):
    """Test GET /api/status returns 200 with online status and models."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert "gemma-4-31b-it" in data.get("supported_gemma_models", [])


def test_flask_static_index(client):
    """Test GET / serves NeuroTrace.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"NeuroTrace" in response.data


def test_flask_studies_list(client):
    """Test GET /api/studies lists available benchmarks."""
    response = client.get("/api/studies")
    assert response.status_code == 200
    data = response.get_json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) > 0


def test_flask_load_sample_and_slice(client):
    """Test POST /api/load-sample and subsequent slice and segment endpoints."""
    # 1. Load sample
    load_res = client.post(
        "/api/load-sample",
        json={"sample_id": "BraTS20_Training_001_flair.nii"},
    )
    assert load_res.status_code == 200
    load_data = load_res.get_json()
    assert load_data["status"] == "ok"
    study_id = load_data["study_id"]
    assert study_id in SESSION_STORE

    # 2. Get axial slice
    slice_res = client.get(f"/api/slice/{study_id}/axial/75?overlay=1&mode=contour")
    assert slice_res.status_code == 200
    assert slice_res.content_type == "image/png"
    assert len(slice_res.data) > 1000

    # 3. Chat endpoint
    chat_res = client.post(
        "/api/chat",
        json={"study_id": study_id, "query": "What is the tumor volume?"},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.get_json()
    assert chat_data["status"] == "ok"
    assert "reply" in chat_data

    # 4. 3D WebGL volume html
    v3d_res = client.get(f"/api/volume3d-html/{study_id}")
    assert v3d_res.status_code == 200
    assert b"plotly" in v3d_res.data.lower()

    # 5. Export mask
    mask_res = client.get(f"/api/export-mask/{study_id}")
    assert mask_res.status_code == 200
    assert mask_res.content_type == "application/gzip"

    # 6. Report PDF
    rep_res = client.get(f"/api/report/{study_id}")
    assert rep_res.status_code == 200
    assert rep_res.content_type == "application/pdf"
    assert rep_res.data.startswith(b"%PDF")
