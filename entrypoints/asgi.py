"""The entrypoint for the ASGI (FastAPI) application.

This module is used only by an external ASGI application server like `uvicorn` to start the web
service, including any setup like logging etc. that needs to be completed before the service is
ready to accept requests.

    `uvicorn sapien.entrypoints.asgi:app --reload`

"""

from sapien.core.logging import setup_logging
from sapien.entrypoints.api.app import app

__all__ = ["app"]

setup_logging()
