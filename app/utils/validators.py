from app.exceptions import NotFoundError


async def ensure_section_exists(db, section_id: str | None) -> None:
    """Raise 404 if a section_id was supplied but doesn't exist. No-op when None."""
    if section_id is None:
        return
    if not await db.sections.find_one({"section_id": section_id}, {"_id": 1}):
        raise NotFoundError("Section", section_id)