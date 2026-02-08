from fastapi import APIRouter, HTTPException

from lemonapi.utils.cache import cache_result
from lemonapi.utils.services.note_service import NoteServiceDep

router = APIRouter()


@router.get("/item/{slug}")
@cache_result("notes:{slug}")
async def get_note(slug: str, notes: NoteServiceDep):
    """
    Get a note by its slug.

    Args:
        slug: The slug of the note to retrieve.
        notes: The note service dependency.

    Returns:
        The note data.

    Raises:
        HTTPException: If the note is not found.
    """
    note = await notes.get_note_by_slug(slug)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/notes/all")
@cache_result("notes:all")
async def get_all_notes(notes: NoteServiceDep):
    """
    Get all notes.

    Args:
        notes: The note service dependency.

    Returns:
        List of all notes.
    """
    return await notes.get_all_notes()


@router.get("/tags/all")
@cache_result("tags:all")
async def get_all_tags(notes: NoteServiceDep):
    """
    Get all unique tags from all notes.

    Args:
        notes: The note service dependency.

    Returns:
        List of all unique tags.
    """
    return await notes.get_all_tags()
