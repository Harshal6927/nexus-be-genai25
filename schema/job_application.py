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


class CandidateUpdate(Struct):
    data_processed: bool = False
    candidate_image: str | None = None
    candidate_resume_data: str | None = None
    candidate_linkedin_data: str | None = None
    candidate_github_data: str | None = None
    candidate_portfolio_data: str | None = None


class JobApplicationsResponse(Struct):
    job_id: int
    candidate_id: int
    candidate_skills: str | None
    candidate_summary: str | None
    id: int
    created_at: datetime
    updated_at: datetime


class JobApplicationUpdate(Struct):
    candidate_skills: str | None = None
    candidate_summary: str | None = None
