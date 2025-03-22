from __future__ import annotations

from typing import Annotated

from advanced_alchemy.extensions.litestar import providers
from litestar import Controller, delete, get, post
from litestar.params import Dependency
from litestar.plugins.sqlalchemy import repository, service

from models import Job
from schema.job import JobCreate, JobResponse


class JobService(service.SQLAlchemyAsyncRepositoryService[Job]):
    class Repo(repository.SQLAlchemyAsyncRepository[Job]):
        model_type = Job

    repository_type = Repo


class JobController(Controller):
    path = "/jobs"

    dependencies = providers.create_service_dependencies(
        JobService,
        key="job_service",
        filters={"pagination_type": "limit_offset", "pagination_size": 20},
    )

    @get("/")
    async def get_jobs(
        self,
        filters: Annotated[list[service.FilterTypeT], Dependency(skip_validation=True)],
        job_service: JobService,
    ) -> service.OffsetPagination[JobResponse]:
        objs, total = await job_service.list_and_count(*filters)
        return job_service.to_schema(objs, total, schema_type=JobResponse)

    @get("/{job_id:int}")
    async def get_job_details(self, job_id: int, job_service: JobService) -> JobResponse:
        obj = await job_service.get(job_id)
        return job_service.to_schema(obj, schema_type=JobResponse)

    @post("/")
    async def create_job(self, data: JobCreate, job_service: JobService) -> JobResponse:
        obj = await job_service.create(data)
        return job_service.to_schema(obj, schema_type=JobResponse)

    @delete("/{job_id:int}", status_code=200)
    async def delete_job(self, job_id: int, job_service: JobService) -> JobResponse:
        obj = await job_service.delete(job_id)
        return job_service.to_schema(obj, schema_type=JobResponse)
