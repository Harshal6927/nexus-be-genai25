from datetime import datetime

from msgspec import Struct


class CandidateCreate(Struct):
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    candidate_current_role: str
    candidate_current_yoe: int
    candidate_resume_id: str
    candidate_linkedin: str
    candidate_github: str | None = None
    candidate_portfolio: str | None = None


class JobApplicationsResponse(Struct):
    job_id: int
    candidate_id: int
    candidate_skills: str | None
    candidate_summary: str | None
    id: int
    created_at: datetime
    updated_at: datetime
