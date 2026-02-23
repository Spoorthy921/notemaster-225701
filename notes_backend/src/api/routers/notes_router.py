from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from src.api.db import get_db
from src.api.deps import get_current_user
from src.api.models import AppUser, Note, NoteTag, Tag
from src.api.schemas import NoteCreate, NoteOut, NotesListResponse, NoteUpdate, TagOut

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _get_or_create_tags(db: Session, user_id: UUID, names: list[str]) -> list[Tag]:
    normalized = []
    seen = set()
    for n in names:
        name = (n or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(name)

    if not normalized:
        return []

    existing = db.execute(
        select(Tag).where(Tag.user_id == user_id, func.lower(Tag.name).in_([n.lower() for n in normalized]))
    ).scalars().all()
    existing_by_lower = {t.name.lower(): t for t in existing}

    result: list[Tag] = []
    for name in normalized:
        t = existing_by_lower.get(name.lower())
        if t is None:
            t = Tag(user_id=user_id, name=name)
            db.add(t)
            db.flush()  # allocate id without committing
        result.append(t)
    return result


def _note_to_out(note: Note) -> NoteOut:
    tags = [TagOut(id=nt.tag.id, name=nt.tag.name) for nt in note.note_tags]
    return NoteOut(
        id=note.id,
        title=note.title,
        content_markdown=note.content_markdown,
        is_pinned=note.is_pinned,
        is_favorite=note.is_favorite,
        created_at=note.created_at,
        updated_at=note.updated_at,
        tags=tags,
    )


@router.get(
    "",
    response_model=NotesListResponse,
    summary="List notes",
    description="List notes for the authenticated user with optional search and filters.",
    operation_id="notes_list",
)
def list_notes(
    q: str | None = Query(default=None, description="Search query matched against title/content"),
    tag: str | None = Query(default=None, description="Filter notes that have the given tag name"),
    pinned: bool | None = Query(default=None, description="Filter pinned notes"),
    favorite: bool | None = Query(default=None, description="Filter favorite notes"),
    limit: int = Query(default=50, ge=1, le=200, description="Max items"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotesListResponse:
    """Return a filtered, ordered list of notes."""
    stmt = (
        select(Note)
        .where(Note.user_id == user.id)
        .options(joinedload(Note.note_tags).joinedload(NoteTag.tag))
    )

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Note.title.ilike(like), Note.content_markdown.ilike(like)))

    if pinned is not None:
        stmt = stmt.where(Note.is_pinned == pinned)

    if favorite is not None:
        stmt = stmt.where(Note.is_favorite == favorite)

    if tag:
        stmt = stmt.join(NoteTag).join(Tag).where(Tag.user_id == user.id, func.lower(Tag.name) == tag.lower())

    # Pinned first, then updated desc
    stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    notes = db.execute(stmt.limit(limit).offset(offset)).unique().scalars().all()

    return NotesListResponse(items=[_note_to_out(n) for n in notes], total=int(total))


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a note with optional tags.",
    operation_id="notes_create",
)
def create_note(
    payload: NoteCreate,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteOut:
    """Create a new note."""
    note = Note(
        user_id=user.id,
        title=payload.title or "",
        content_markdown=payload.content_markdown or "",
        is_pinned=bool(payload.is_pinned),
        is_favorite=bool(payload.is_favorite),
    )
    db.add(note)
    db.flush()

    tags = _get_or_create_tags(db, user.id, payload.tags)
    for t in tags:
        db.add(NoteTag(note_id=note.id, tag_id=t.id))

    db.commit()
    note = db.execute(
        select(Note)
        .where(Note.id == note.id)
        .options(joinedload(Note.note_tags).joinedload(NoteTag.tag))
    ).unique().scalar_one()
    return _note_to_out(note)


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get note",
    description="Fetch a single note by id.",
    operation_id="notes_get",
)
def get_note(
    note_id: UUID,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteOut:
    """Fetch a single note."""
    note = db.execute(
        select(Note)
        .where(Note.id == note_id, Note.user_id == user.id)
        .options(joinedload(Note.note_tags).joinedload(NoteTag.tag))
    ).unique().scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return _note_to_out(note)


@router.patch(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update note",
    description="Update note fields; when tags is provided, it replaces the note's tag set.",
    operation_id="notes_update",
)
def update_note(
    note_id: UUID,
    payload: NoteUpdate,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteOut:
    """Update a note."""
    note = db.execute(
        select(Note)
        .where(Note.id == note_id, Note.user_id == user.id)
        .options(joinedload(Note.note_tags).joinedload(NoteTag.tag))
    ).unique().scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if payload.title is not None:
        note.title = payload.title
    if payload.content_markdown is not None:
        note.content_markdown = payload.content_markdown
    if payload.is_pinned is not None:
        note.is_pinned = payload.is_pinned
    if payload.is_favorite is not None:
        note.is_favorite = payload.is_favorite

    if payload.tags is not None:
        # replace tags
        db.query(NoteTag).filter(NoteTag.note_id == note.id).delete(synchronize_session=False)
        tags = _get_or_create_tags(db, user.id, payload.tags)
        for t in tags:
            db.add(NoteTag(note_id=note.id, tag_id=t.id))

    db.commit()

    note = db.execute(
        select(Note)
        .where(Note.id == note.id)
        .options(joinedload(Note.note_tags).joinedload(NoteTag.tag))
    ).unique().scalar_one()
    return _note_to_out(note)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Delete a note by id.",
    operation_id="notes_delete",
)
def delete_note(
    note_id: UUID,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a note."""
    note = db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    db.delete(note)
    db.commit()
    return None
