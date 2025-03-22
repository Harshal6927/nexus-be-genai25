from enum import StrEnum

from litestar.plugins.sqlalchemy import base
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column


class GenAIModel(StrEnum):
    GEMINI_2_0_FLASH = "gemini-2.0-flash-001"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"


class JobType(StrEnum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class Agent(base.BigIntAuditBase):
    __tablename__ = "agent"

    agent_name: Mapped[str] = mapped_column(unique=True)
    agent_instructions: Mapped[str] = mapped_column(nullable=True)


class Job(base.BigIntAuditBase):
    __tablename__ = "job"

    job_title: Mapped[str] = mapped_column()
    job_location: Mapped[str] = mapped_column()
    job_type: Mapped[JobType] = mapped_column(default=JobType.FULL_TIME)
    job_description: Mapped[str] = mapped_column(type_=TEXT)
    job_requirements: Mapped[str] = mapped_column(type_=TEXT)
    job_contact_email: Mapped[str] = mapped_column()


class Candidate(base.BigIntAuditBase):
    __tablename__ = "candidate"

    candidate_name: Mapped[str] = mapped_column()
    candidate_email: Mapped[str] = mapped_column()
    candidate_phone: Mapped[str] = mapped_column()
    candidate_current_role: Mapped[str] = mapped_column()
    candidate_current_yoe: Mapped[int] = mapped_column()
    candidate_resume_id: Mapped[str] = mapped_column()
    candidate_linkedin: Mapped[str] = mapped_column()
    candidate_github: Mapped[str] = mapped_column()
    candidate_portfolio: Mapped[str] = mapped_column()
    data_processed: Mapped[bool] = mapped_column(default=False)
    # metadata
    candidate_image: Mapped[str] = mapped_column(nullable=True)
    candidate_resume_data: Mapped[str] = mapped_column(type_=TEXT, nullable=True)
    candidate_linkedin_data: Mapped[str] = mapped_column(type_=TEXT, nullable=True)
    candidate_github_data: Mapped[str] = mapped_column(type_=TEXT, nullable=True)
    candidate_portfolio_data: Mapped[str] = mapped_column(type_=TEXT, nullable=True)


class JobApplication(base.BigIntAuditBase):
    __tablename__ = "job_application"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="unique_job_application"),)

    job_id: Mapped[int] = mapped_column(ForeignKey("job.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id", ondelete="CASCADE"), index=True)
    candidate_skills: Mapped[str] = mapped_column(nullable=True)
    candidate_summary: Mapped[str] = mapped_column(nullable=True)
