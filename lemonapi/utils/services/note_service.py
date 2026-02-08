import json
from pathlib import Path
from typing import List, Optional, Annotated
from fastapi import Depends
from loguru import logger

from .. import dependencies
from ..cache import _serialize
from ..constants import Server


class NoteService:
    """
    Service class for CRUD operations on notes.
    """

    def __init__(self, pool: dependencies.PoolDep):
        """
        Initialize the NoteService with a database connection pool.

        Args:
            pool: Database connection pool dependency.
        """
        self.pool = pool

    async def get_note_by_slug(self, slug: str) -> Optional[dict]:
        """
        Get a note by its slug.

        Args:
            slug: The slug of the note.

        Returns:
            The note as a dictionary if found, None otherwise.
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM notes WHERE slug = $1", slug)
            return dict(row) if row else None

    async def get_all_notes(self) -> List[dict]:
        """
        Get all notes from the database, importing Obsidian notes first.

        Returns:
            List of all notes as dictionaries.
        """
        await self.import_obsidian_notes(Server.IMPORT_NOTES_PATH)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM notes")
            return [dict(r) for r in rows]

    async def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all notes.

        Returns:
            Sorted list of unique tags.
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT tags FROM notes")
            all_tags = []
            for r in rows:
                if r["tags"]:
                    all_tags.extend(r["tags"])
            return sorted(set(all_tags))

    async def create_note(
        self, title: str, slug: str, content: str, tags: Optional[List[str]] = None
    ) -> dict:
        """
        Create a new note in the database.

        Args:
            title: The title of the note.
            slug: The slug of the note.
            content: The content of the note.
            tags: Optional list of tags for the note.

        Returns:
            The created note as a dictionary.
        """
        tags_json = json.dumps(tags) if tags else None

        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO notes (title, slug, content, tags) VALUES ($1, $2, $3, $4)",
                title,
                slug,
                content,
                tags_json,
            )
            note = await self.get_note_by_slug(slug)
            logger.info(f"Note '{slug}' created")
        return note

    async def import_obsidian_notes(self, base_dir: Optional[Path] = None):
        """
        Scan a directory for files with allowed extensions and import them as notes.

        Scans the pre-defined notes directory (or base_dir) for files with allowed extensions
        and inserts them into the DB if not already present.

        Args:
            base_dir: The base directory to scan. Defaults to Server.NOTES_IMPORT_PATH.
        """
        base_dir = base_dir or Server.NOTES_IMPORT_PATH

        for file_path in base_dir.rglob("*"):  # scan all files
            if file_path.suffix.lower() not in Server.IMPORT_NOTE_EXTENSIONS:
                continue  # skip non-allowed extensions

            slug = file_path.stem
            title = slug.replace("-", " ").replace("_", " ").title()
            tags = list(file_path.relative_to(base_dir).parts[:-1])

            existing = await self.get_note_by_slug(slug)
            if existing:
                continue

            content = file_path.read_text(encoding="utf-8")
            await self.create_note(title=title, slug=slug, content=content, tags=tags)
            logger.info(f"Imported note '{slug}' from {base_dir}")

    async def search_notes(self, q: str) -> dict:
        """
        Search notes using full-text search.

        Returns exact and inexact matches based on query length.

        Args:
            q: The search query.

        Returns:
            Dictionary with exact_results and inexact_results lists.
        """
        async with self.pool.acquire() as conn:
            # Exact match using plainto_tsquery
            exact_query = """
                SELECT *, ts_rank(tsv, plainto_tsquery('english', $1)) AS rank
                FROM notes
                WHERE tsv @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT 20
            """
            exact_rows = await conn.fetch(exact_query, q)
            exact_results = [_serialize(dict(r)) for r in exact_rows]

            inexact_results = None
            if len(q) >= 3:
                inexact_query = """
                    SELECT *, ts_rank(tsv, to_tsquery('english', $1 || ':*')) AS rank
                    FROM notes
                    WHERE tsv @@ to_tsquery('english', $1 || ':*')
                    ORDER BY rank DESC
                    LIMIT 20
                """
                inexact_rows = await conn.fetch(inexact_query, q)
                inexact_results = [_serialize(dict(r)) for r in inexact_rows]

            if not exact_results and (inexact_results is None or not inexact_results):
                return {"exact_results": [], "inexact_results": []}

        return {"exact_results": exact_results, "inexact_results": inexact_results}


NoteServiceDep = Annotated[NoteService, Depends(NoteService)]