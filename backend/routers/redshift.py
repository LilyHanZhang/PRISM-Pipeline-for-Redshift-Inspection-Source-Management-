from fastapi import APIRouter, HTTPException
from backend import config
from backend.state import get_tags_db, save_tags_db

router = APIRouter(prefix="/api/redshift", tags=["redshift"])


@router.patch("/{source_id}")
def update_z_spec(source_id: str, body: dict):
    """Update z_spec for a source."""
    z_spec = body.get("z_spec")
    if z_spec is None:
        raise HTTPException(status_code=400, detail="z_spec is required")

    try:
        z_spec = float(z_spec)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="z_spec must be a number")

    db = get_tags_db()
    if "sources" not in db:
        db["sources"] = {}
    if source_id not in db["sources"]:
        db["sources"][source_id] = {"tags": [], "z_spec": None, "notes": ""}

    db["sources"][source_id]["z_spec"] = z_spec
    save_tags_db(db)

    return {"status": "ok", "z_spec": z_spec}
