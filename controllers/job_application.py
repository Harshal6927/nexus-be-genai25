from __future__ import annotations

from advanced_alchemy.extensions.litestar import providers
from litestar import Controller, MediaType, Response, delete, get, post, status_codes
from litestar.plugins.sqlalchemy import repository, service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Candidate, Job, JobApplication
from schema.job_application import CandidateCreate, JobApplicationsResponse


class JobApplicationService(service.SQLAlchemyAsyncRepositoryService[JobApplication]):
    class Repo(repository.SQLAlchemyAsyncRepository[JobApplication]):
        model_type = JobApplication

    repository_type = Repo


class JobApplicationController(Controller):
    path = "/job-applications"

    dependencies = providers.create_service_dependencies(
        JobApplicationService,
        key="job_applications_service",
    )

    @get("/")
    async def get_all_job_applications(
        self,
        job_applications_service: JobApplicationService,
    ) -> service.OffsetPagination[JobApplicationsResponse]:
        obj = await job_applications_service.list()
        return job_applications_service.to_schema(obj, schema_type=JobApplicationsResponse)

    @delete("/{job_application_id:int}", status_code=200)
    async def delete_job_application(
        self,
        job_application_id: int,
        job_applications_service: JobApplicationService,
    ) -> JobApplicationsResponse:
        obj = await job_applications_service.delete(job_application_id)
        return job_applications_service.to_schema(obj, schema_type=JobApplicationsResponse)

    # candidate application
    @post("/apply/{job_id:int}")
    async def job_apply(self, job_id: int, data: CandidateCreate, db_session: AsyncSession) -> Response:
        job = await db_session.scalar(
            select(Job).where(Job.id == job_id),
        )
        if job is None:
            return Response(
                status_code=status_codes.HTTP_404_NOT_FOUND,
                media_type=MediaType.JSON,
                content={"status": "error", "message": "Job not found"},
            )

        candidate = Candidate(
            candidate_name=data.candidate_name,
            candidate_email=data.candidate_email,
            candidate_phone=data.candidate_phone,
            candidate_current_role=data.candidate_current_role,
            candidate_current_yoe=data.candidate_current_yoe,
            candidate_resume_id=data.candidate_resume_id,
            candidate_linkedin=data.candidate_linkedin,
            candidate_github=data.candidate_github,
            candidate_portfolio=data.candidate_portfolio,
        )
        db_session.add(candidate)
        await db_session.flush()

        job_application = JobApplication(
            job_id=job_id,
            candidate_id=candidate.id,
        )
        db_session.add(job_application)

        return Response(
            status_code=status_codes.HTTP_200_OK,
            media_type=MediaType.JSON,
            content={"status": "success", "message": "Job applied successfully"},
        )

    @get("/{job_id:int}")
    async def get_job_applications(self, job_id: int, db_session: AsyncSession) -> Response:
        query = (
            select(
                JobApplication.id,
                Candidate.candidate_name,
                Candidate.candidate_email,
                Candidate.candidate_phone,
                Candidate.candidate_current_yoe,
                Candidate.candidate_current_role,
                Candidate.candidate_resume_id,
                Candidate.data_processed,
                Candidate.candidate_image,
                JobApplication.created_at,
                JobApplication.candidate_summary,
                JobApplication.candidate_skills,
            )
            .join(Candidate, JobApplication.candidate_id == Candidate.id)
            .where(JobApplication.job_id == job_id)
        )

        result = await db_session.execute(query)
        applications = []

        for row in result:
            # TODO: call the GENAI API to get the progress
            application = {
                "id": row.id,
                "candidate_name": row.candidate_name,
                "candidate_email": row.candidate_email,
                "candidate_phone": row.candidate_phone,
                "candidate_current_yoe": row.candidate_current_yoe,
                "candidate_current_role": row.candidate_current_role,
                "candidate_resume": row.candidate_resume_id,
                "applied_date": row.created_at.isoformat(),
                "data_processed": row.data_processed,
                "progress": 0,
                "summary": row.candidate_summary,
                "avatar": row.candidate_image,
                "skills": row.candidate_skills or [],
            }
            applications.append(application)

        return Response(
            status_code=status_codes.HTTP_200_OK,
            media_type=MediaType.JSON,
            content={
                "status": "success",
                "job_applications": applications,
            },
        )
