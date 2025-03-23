from __future__ import annotations

import os

import google.generativeai as GOOGLE_GENAI
import minio
from dotenv import load_dotenv
from google.generativeai.types import generation_types
from litestar import MediaType, Request, Response, status_codes
from litestar.config.cors import CORSConfig
from litestar.exceptions.http_exceptions import ValidationException
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig
from litestar_saq import CronJob, QueueConfig, SAQConfig, SAQPlugin

load_dotenv()

# openapi
OPENAPI_CONFIG = OpenAPIConfig(
    title="My API",
    version="0.0.1",
    render_plugins=[ScalarRenderPlugin()],
)

# cors
CORS_CONFIG = CORSConfig(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# database
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if DB_HOST and DB_PORT and DB_NAME and DB_USER and DB_PASSWORD:
    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DATABASE_URL_SAQ = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    raise ValueError("Database environment variables not set")

DB_CONFIG = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    create_all=True,
    before_send_handler="autocommit",
)

# genai
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    GOOGLE_GENAI.configure(api_key=GEMINI_API_KEY)  # type: ignore
else:
    raise ValueError("GEMINI_API_KEY environment variable not set")

GENERATION_CONFIG = generation_types.GenerationConfig(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)

# minio
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")
if MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY:
    MINIO_CLIENT = minio.Minio(
        MINIO_ENDPOINT,
        MINIO_ACCESS_KEY,
        MINIO_SECRET_KEY,
        secure=False,
    )
else:
    raise ValueError("Minio environment variables not set")

# saq
SAQ = SAQPlugin(
    config=SAQConfig(
        web_enabled=True,
        use_server_lifespan=True,
        queue_configs=[
            QueueConfig(
                dsn=DATABASE_URL_SAQ,
                name="candidate_data_processing",
                scheduled_tasks=[
                    CronJob(
                        function="utils.candidate.process_candidate",
                        cron="* * * * *",
                        timeout=600,
                        ttl=2000,
                    ),
                ],
            ),
        ],
    ),
)


# exception handler
def exception_handler(_: Request, exc: ValidationException | Exception) -> Response:
    status_code = getattr(
        exc,
        "status_code",
        status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    if isinstance(exc, ValidationException):
        if isinstance(exc.extra, list):
            detail = f"Validation error: {exc.extra[0]['message']}"
        else:
            detail = f"Validation error: {exc.extra}"
    else:
        detail = getattr(exc, "detail", str(exc))

    return Response(
        status_code=status_code,
        media_type=MediaType.JSON,
        content={"status": "error", "message": detail},
    )
