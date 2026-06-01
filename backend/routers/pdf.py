import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend import config

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.get("/{source_id}/{filter_name}/{orient}")
def get_pdf(source_id: str, filter_name: str, orient: str):
    """Stream the PDF for a specific filter × orientation."""
    pdf_filename = config.PDF_PATTERN.format(
        field=config.FIELD_NAME,
        filter=filter_name,
        id=source_id,
        orient=orient,
    )
    pdf_path = os.path.join(config.DATA_ROOT, config.PDF_DIR, pdf_filename)

    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404,
            detail=f"PDF not found for {source_id} {filter_name} {orient}",
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_filename,
    )
