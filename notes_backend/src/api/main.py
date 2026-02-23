from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_settings
from src.api.routers.auth_router import router as auth_router
from src.api.routers.notes_router import router as notes_router
from src.api.routers.tags_router import router as tags_router

openapi_tags = [
    {"name": "meta", "description": "Health and documentation endpoints"},
    {"name": "auth", "description": "Authentication endpoints (signup/login)"},
    {"name": "notes", "description": "Create, update, delete, list notes"},
    {"name": "tags", "description": "Tag listing for sidebar/filtering"},
]

app = FastAPI(
    title="NoteMaster API",
    description="Backend API for a fullstack Notes app (notes, tags, search, pin/favorite, markdown).",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin] if settings.frontend_origin != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"], summary="Health check", description="Simple health check.", operation_id="health_check")
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(tags_router)
