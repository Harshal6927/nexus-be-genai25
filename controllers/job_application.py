from __future__ import annotations

from contextlib import suppress
from datetime import timedelta

from advanced_alchemy.extensions.litestar import providers
from google.cloud import storage
from litestar import Controller, MediaType, Response, delete, get, post, put, status_codes
from litestar.plugins.sqlalchemy import repository, service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import GENERATION_CONFIG, GOOGLE_GENAI
from models import Agent, Candidate, GenAIModel, Job, JobApplication
from schema.job_application import CandidateCreate, CandidateUpdate, JobApplicationsResponse, JobApplicationUpdate


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
        db_session: AsyncSession,
    ) -> JobApplicationsResponse:
        obj = await job_applications_service.delete(job_application_id)

        candidate = await db_session.scalar(
            select(Candidate).where(Candidate.id == obj.candidate_id),
        )

        if candidate is None:
            raise ValueError("Candidate not found")

        await db_session.delete(candidate)

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

    @get("/signed-url/{blob_name:str}")
    async def get_signed_url(self, blob_name: str) -> str:
        storage_client = storage.Client()
        bucket = storage_client.bucket("nexus-genai25")
        blob = bucket.blob(blob_name)

        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=30),
            method="PUT",
        )

    @get("/{job_id:int}/{agent_id:int}/{genai_model:str}")
    async def get_job_applications(
        self,
        job_id: int,
        agent_id: int,
        genai_model: str,
        db_session: AsyncSession,
    ) -> Response:
        _ = GenAIModel(genai_model)

        agent = await db_session.scalar(select(Agent).where(Agent.id == agent_id))

        if agent is None:
            return Response(
                status_code=status_codes.HTTP_404_NOT_FOUND,
                media_type=MediaType.JSON,
                content={"status": "error", "message": "Agent not found"},
            )

        job = await db_session.scalar(select(Job).where(Job.id == job_id))

        if job is None:
            return Response(
                status_code=status_codes.HTTP_404_NOT_FOUND,
                media_type=MediaType.JSON,
                content={"status": "error", "message": "Job not found"},
            )

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
                Candidate.candidate_resume_data,
                Candidate.candidate_linkedin_data,
                Candidate.candidate_github_data,
                Candidate.candidate_portfolio_data,
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
            system_instruction = f"SYSTEM: You are a AI agent named {agent.agent_name} helping recruiters to process the candidate applications. Your task is to analyze the provided candidate information and generate how much the candidate is suitable for the job. The higher the number, the more suitable the candidate is for the job.\n\nAGENT_INSTRUCTION: {agent.agent_instructions}\n\nJOB_DESCRIPTION: {job.job_description}\n\nJOB_REQUIREMENTS: {job.job_requirements}\n\nSYSTEM: Keep in mind that you can only reply with a number between 0 to 100 one time"

            model = GOOGLE_GENAI.GenerativeModel(  # type: ignore
                model_name="gemini-1.5-flash-8b",
                generation_config=GENERATION_CONFIG,
                system_instruction=system_instruction,
            )

            chat_session = model.start_chat()

            candidate_data = f"**RESUME:** {row.candidate_resume_data}\n\n\n\n**LINKEDIN:** {row.candidate_linkedin_data}\n\n\n\n**GITHUB:** {row.candidate_github_data}\n\n\n\n**PORTFOLIO:** {row.candidate_portfolio_data}"

            response = await chat_session.send_message_async(candidate_data)

            progress = 0
            if response.text:
                with suppress(ValueError):
                    progress = int(response.text)

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
                "progress": progress,
                "summary": row.candidate_summary,
                "avatar": row.candidate_image,
                "skills": eval(row.candidate_skills) if row.candidate_skills else [],
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

    @put("/candidate/{candidate_id:int}")
    async def update_candidate(
        self,
        candidate_id: int,
        data: CandidateUpdate,
        db_session: AsyncSession,
    ) -> Response:
        candidate = await db_session.scalar(
            select(Candidate).where(Candidate.id == candidate_id),
        )

        if candidate is None:
            return Response(
                status_code=status_codes.HTTP_404_NOT_FOUND,
                media_type=MediaType.JSON,
                content={"status": "error", "message": "Candidate not found"},
            )

        candidate.data_processed = data.data_processed
        candidate.candidate_image = data.candidate_image  # type: ignore
        candidate.candidate_resume_data = data.candidate_resume_data  # type: ignore
        candidate.candidate_linkedin_data = data.candidate_linkedin_data  # type: ignore
        candidate.candidate_github_data = data.candidate_github_data  # type: ignore
        candidate.candidate_portfolio_data = data.candidate_portfolio_data  # type: ignore

        return Response(
            status_code=status_codes.HTTP_200_OK,
            media_type=MediaType.JSON,
            content={"status": "success", "message": "Candidate updated successfully"},
        )

    @put("/{job_application_id:int}")
    async def update_job_application(
        self,
        job_application_id: int,
        data: JobApplicationUpdate,
        job_applications_service: JobApplicationService,
    ) -> JobApplicationsResponse:
        obj = await job_applications_service.update(data=data, item_id=job_application_id)
        return job_applications_service.to_schema(obj, schema_type=JobApplicationsResponse)

    @get("/{candidate_id:int}")
    async def get_job_application(
        self,
        candidate_id: int,
        db_session: AsyncSession,
    ) -> JobApplicationsResponse:
        job_application = await db_session.scalar(
            select(JobApplication).where(JobApplication.candidate_id == candidate_id),
        )

        if job_application is None:
            raise ValueError("Job application not found")

        return JobApplicationsResponse(
            job_id=job_application.job_id,
            candidate_id=job_application.candidate_id,
            candidate_skills=job_application.candidate_skills,
            candidate_summary=job_application.candidate_summary,
            id=job_application.id,
            created_at=job_application.created_at,
            updated_at=job_application.updated_at,
        )
