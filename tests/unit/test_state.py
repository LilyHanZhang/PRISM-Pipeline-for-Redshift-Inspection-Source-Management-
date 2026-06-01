import pytest
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestState:
    def test_load_tags_db_nonexistent(self, monkeypatch, tmp_path):
        db_path = tmp_path / "tags_db.json"
        monkeypatch.setattr("backend.config.TAGS_DB_PATH", str(db_path))

        import importlib
        import backend.state
        importlib.reload(backend.state)

        from backend.state import _load_tags_db
        result = _load_tags_db()
        assert result == {"sources": {}}

    def test_load_tags_db_valid(self, monkeypatch, tmp_path):
        db_path = tmp_path / "tags_db.json"
        db_content = {
            "sources": {
                "133": {"tags": ["galaxy"], "z_spec": 1.19, "notes": ""}
            }
        }
        db_path.write_text(json.dumps(db_content))
        monkeypatch.setattr("backend.config.TAGS_DB_PATH", str(db_path))

        import importlib
        import backend.state
        importlib.reload(backend.state)

        from backend.state import _load_tags_db
        result = _load_tags_db()
        assert "133" in result["sources"]
        assert result["sources"]["133"]["tags"] == ["galaxy"]

    def test_save_tags_db_creates_backup(self, monkeypatch, tmp_path):
        db_path = tmp_path / "tags_db.json"
        db_path.write_text(json.dumps({"sources": {}}))
        monkeypatch.setattr("backend.config.TAGS_DB_PATH", str(db_path))

        import importlib
        import backend.state
        importlib.reload(backend.state)

        from backend.state import save_tags_db

        new_db = {"sources": {"133": {"tags": ["new"], "z_spec": None, "notes": ""}}}
        save_tags_db(new_db)

        assert (tmp_path / "tags_db.json.bak").exists()

    def test_save_tags_db_writes_correctly(self, monkeypatch, tmp_path):
        db_path = tmp_path / "tags_db.json"
        monkeypatch.setattr("backend.config.TAGS_DB_PATH", str(db_path))

        import importlib
        import backend.state
        importlib.reload(backend.state)

        from backend.state import save_tags_db, _load_tags_db

        new_db = {"sources": {"203": {"tags": ["AGN"], "z_spec": 2.34, "notes": "test"}}}
        save_tags_db(new_db)

        loaded = _load_tags_db()
        assert loaded["sources"]["203"]["tags"] == ["AGN"]
        assert loaded["sources"]["203"]["z_spec"] == 2.34

    def test_scan_source_flags_empty_catalog(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import importlib
        import backend.config
        importlib.reload(backend.config)

        (tmp_path / "sapphires_edr_1d_spec").mkdir()
        (tmp_path / "sapphires_edr_2d_spec").mkdir()
        (tmp_path / "sapphires_edr_spec_pdf").mkdir()

        import backend.state
        importlib.reload(backend.state)

        from backend.state import _scan_source_flags

        backend.state._merged_catalog = None
        result = _scan_source_flags()
        assert result == {}
