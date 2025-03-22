from datetime import datetime

from msgspec import Struct

from models import JobType


class JobCreate(Struct):
    job_title: str
    job_location: str
    job_type: JobType
    job_description: str
    job_requirements: str
    job_contact_email: str


class JobResponse(Struct):
    job_title: str
    job_location: str
    job_type: JobType
    job_description: str
    job_requirements: str
    job_contact_email: str
    id: int
    created_at: datetime
    updated_at: datetime
