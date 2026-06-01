import os
import csv
import io
import json
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend import config
from backend.state import get_tags_db, save_tags_db

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/list")
def get_tag_list():
    """Vocabulary of all defined tags."""
    return config.TAG_VOCABULARY


@router.get("/source/{source_id}")
def get_source_tags(source_id: str):
    """Get tags for a specific source."""
    db = get_tags_db()
    source_data = db.get("sources", {}).get(source_id, {})
    return source_data.get("tags", [])


@router.post("/{source_id}/add")
def add_tag(source_id: str, body: dict):
    """Add a tag to a source."""
    tag = body.get("tag", "")
    if not tag:
        raise HTTPException(status_code=400, detail="Tag is required")

    db = get_tags_db()
    if "sources" not in db:
        db["sources"] = {}
    if source_id not in db["sources"]:
        db["sources"][source_id] = {"tags": [], "z_spec": None, "notes": ""}

    if tag not in db["sources"][source_id]["tags"]:
        db["sources"][source_id]["tags"].append(tag)
        save_tags_db(db)

    return {"status": "ok", "tags": db["sources"][source_id]["tags"]}


@router.delete("/{source_id}/remove")
def remove_tag(source_id: str, body: dict):
    """Remove a tag from a source."""
    tag = body.get("tag", "")
    if not tag:
        raise HTTPException(status_code=400, detail="Tag is required")

    db = get_tags_db()
    source_data = db.get("sources", {}).get(source_id, {})
    tags = source_data.get("tags", [])

    if tag in tags:
        db["sources"][source_id]["tags"].remove(tag)
        save_tags_db(db)

    return {"status": "ok", "tags": db.get("sources", {}).get(source_id, {}).get("tags", [])}


@router.post("/bulk")
async def bulk_import(
    file: UploadFile = File(...),
    id_column: str = Form(default="ID"),
    tag: str = Form(default=""),
):
    """Bulk import tags from a .txt or .csv file."""
    if not tag:
        raise HTTPException(status_code=400, detail="Tag is required")

    content = await file.read()
    text = content.decode("utf-8")

    ids_to_tag = []
    if text.strip().startswith("ID,") or text.strip().startswith("id,"):
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            if id_column in row:
                ids_to_tag.append(str(row[id_column]).strip())
    else:
        for line in text.strip().split("\n"):
            line = line.strip()
            if line:
                ids_to_tag.append(line)

    db = get_tags_db()
    if "sources" not in db:
        db["sources"] = {}

    matched = 0
    not_found = []

    for sid in ids_to_tag:
        if sid in db["sources"]:
            if tag not in db["sources"][sid].get("tags", []):
                db["sources"][sid].setdefault("tags", []).append(tag)
            matched += 1
        else:
            not_found.append(sid)

    save_tags_db(db)
    return {"matched": matched, "not_found": not_found}
