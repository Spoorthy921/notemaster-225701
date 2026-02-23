from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.deps import get_current_user
from src.api.models import AppUser, Tag
from src.api.schemas import TagOut

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get(
    "",
    response_model=list[TagOut],
    summary="List tags",
    description="List all tags for the authenticated user.",
    operation_id="tags_list",
)
def list_tags(user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TagOut]:
    """Return all tags for the current user."""
    tags = db.execute(select(Tag).where(Tag.user_id == user.id).order_by(Tag.name.asc())).scalars().all()
    return tags
