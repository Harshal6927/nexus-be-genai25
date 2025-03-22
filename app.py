from __future__ import annotations

from litestar import Litestar, get
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from saq import Queue

from config import CORS_CONFIG, DB_CONFIG, OPENAPI_CONFIG, SAQ, exception_handler
from controllers.agent import AgentController
from controllers.job import JobController
from controllers.job_application import JobApplicationController


@get("/health-check", sync_to_thread=False)
def index() -> str:
    return "OK"


app = Litestar(
    route_handlers=[
        index,
        AgentController,
        JobApplicationController,
        JobController,
    ],
    cors_config=CORS_CONFIG,
    openapi_config=OPENAPI_CONFIG,
    plugins=[SQLAlchemyPlugin(DB_CONFIG), SAQ],
    exception_handlers={Exception: exception_handler},
    signature_types=[Queue],
    debug=True,
)
