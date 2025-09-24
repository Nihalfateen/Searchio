"""Healthcheck endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["healthcheck"])


@router.get("/")
def healthcheck():
    return {"status": "ok"}
