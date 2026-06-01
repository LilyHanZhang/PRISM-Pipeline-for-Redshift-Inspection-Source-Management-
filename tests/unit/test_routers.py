import pytest
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSourcesRouter:
    def test_health_endpoint(self, app):
        response = app.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_get_sources(self, app):
        response = app.get("/api/sources/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_get_single_source(self, app):
        response = app.get("/api/sources/133")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "133"
        assert "ra" in data
        assert "dec" in data
        assert "has_1d" in data
        assert "has_2d" in data
        assert data["z_spec"] == 1.19

    def test_get_source_without_spec(self, app):
        response = app.get("/api/sources/323")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "323"
        assert data["z_spec"] is None

    def test_get_nonexistent_source(self, app):
        response = app.get("/api/sources/99999")
        assert response.status_code == 404

    def test_search_sources_by_id(self, app):
        response = app.get("/api/sources/search?q=133")
        assert response.status_code == 200
        data = response.json()
        assert "133" in data

    def test_search_sources_empty(self, app):
        response = app.get("/api/sources/search?q=99999")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_sources_near(self, app):
        response = app.get("/api/sources/near?ra=150.123&dec=2.345&r=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["id"] == "133"


class TestTagsRouter:
    def test_get_tag_list(self, app):
        response = app.get("/api/tags/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_add_tag(self, app):
        response = app.post("/api/tags/133/add", json={"tag": "test_tag"})
        assert response.status_code == 200
        data = response.json()
        assert "test_tag" in data["tags"]

    def test_remove_tag(self, app):
        app.post("/api/tags/133/add", json={"tag": "to_remove"})
        response = app.request("DELETE", "/api/tags/133/remove", json={"tag": "to_remove"})
        assert response.status_code == 200
        data = response.json()
        assert "to_remove" not in data["tags"]

    def test_add_empty_tag(self, app):
        response = app.post("/api/tags/133/add", json={"tag": ""})
        assert response.status_code == 400

    def test_get_source_tags(self, app):
        app.post("/api/tags/133/add", json={"tag": "galaxy"})
        response = app.get("/api/tags/source/133")
        assert response.status_code == 200
        data = response.json()
        assert "galaxy" in data


class TestRedshiftRouter:
    def test_update_z_spec(self, app):
        response = app.patch("/api/redshift/133", json={"z_spec": 1.25})
        assert response.status_code == 200
        data = response.json()
        assert data["z_spec"] == 1.25

    def test_update_z_spec_invalid(self, app):
        response = app.patch("/api/redshift/133", json={"z_spec": "not_a_number"})
        assert response.status_code == 400

    def test_update_z_spec_missing(self, app):
        response = app.patch("/api/redshift/133", json={})
        assert response.status_code == 400


class TestPDFRouter:
    def test_pdf_not_found(self, app):
        response = app.get("/api/pdf/133/F356W/R")
        assert response.status_code == 404


class TestImagesRouter:
    def test_get_bands(self, app):
        response = app.get("/api/images/bands")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
