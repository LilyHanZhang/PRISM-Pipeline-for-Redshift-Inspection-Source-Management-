import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend import config
from backend.state import init_state
from backend.routers import sources, spectra, images, pdf, tags, redshift

app = FastAPI(title="PRISM", description="Pipeline for Redshift Inspection & Source Management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router)
app.include_router(spectra.router)
app.include_router(images.router)
app.include_router(pdf.router)
app.include_router(tags.router)
app.include_router(redshift.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup():
    init_state()


static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
