"""The ``/v1`` router — every route, mounted once, with coarse access drawn at the mount."""

from fastapi import APIRouter

from {{pkg}}.api.routes import notes

router = APIRouter(prefix="/v1")

router.include_router(notes.router, prefix="/notes", tags=["notes"])
