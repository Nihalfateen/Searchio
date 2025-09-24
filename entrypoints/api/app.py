from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sapien.entrypoints.api.routes.healthcheck import router as healthcheck_router
from sapien.entrypoints.api.routes.search import router as search_router

app = FastAPI(
    title="My Search Engine", swagger_ui_parameters={"operationsSorter": "alpha"}, prefix="/api/v1"
)

# Get the static files directory path
STATIC_DIR = Path(__file__).parent.parent.parent.parent.parent / "static_pages"

# main API router
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(healthcheck_router)
api_router.include_router(search_router)

# app
app.include_router(api_router)


# Add route to serve the main static page
@app.get("/")
async def serve_index():
    """Serve the main static search page."""
    static_file = STATIC_DIR / "index.html"
    if static_file.exists():
        return FileResponse(static_file)
    return {"message": "Static page not found. Please ensure static_pages/index.html exists."}


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
