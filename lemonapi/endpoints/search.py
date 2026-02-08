from fastapi import APIRouter, HTTPException, Query

from lemonapi.utils.cache import cache_result
from lemonapi.utils.services.note_service import NoteServiceDep

router = APIRouter()


@router.get("/notes/search")
@cache_result(cache_key="search:{q}")
async def search_notes(notes: NoteServiceDep, q: str = Query(..., min_length=1)):
    """
    Search notes by query string.

    This endpoint performs a full-text search using PostgreSQL `tsvector` and `tsquery`.
    The query supports:

    - Exact matches
    - Prefix matches (e.g., `choco*` will match `chocolate`)
    - Logical operators:
        - `&` for AND (both terms must appear)
        - `|` for OR (either term may appear)

    The search results are split into:
    - `exact_results`: notes that match the query exactly
    - `inexact_results`: notes that match a prefix or broader search (optional)

    Caching is applied to improve performance for repeated queries.

    Args:
        q: Query string for searching notes (min length 1).

    Returns:
        A list of notes matching the search query. Raises 404 if no matches are found.
    """
    results = await notes.search_notes(q=q)
    if not results:
        raise HTTPException(status_code=404, detail="No notes found for this query")
    if results["exact_results"]:
        return results["exact_results"]

    return results
