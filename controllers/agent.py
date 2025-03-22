from __future__ import annotations

from advanced_alchemy.extensions.litestar import providers
from litestar import Controller, delete, get, post, put
from litestar.plugins.sqlalchemy import repository, service

from models import Agent
from schema.agent import AgentCreate, AgentResponse, AgentUpdate


class AgentService(service.SQLAlchemyAsyncRepositoryService[Agent]):
    class Repo(repository.SQLAlchemyAsyncRepository[Agent]):
        model_type = Agent

    repository_type = Repo


class AgentController(Controller):
    path = "/agents"

    dependencies = providers.create_service_dependencies(
        AgentService,
        key="agent_service",
    )

    @post("/")
    async def create_agent(
        self,
        data: AgentCreate,
        agent_service: AgentService,
    ) -> AgentResponse:
        obj = await agent_service.create(data)
        return agent_service.to_schema(obj, schema_type=AgentResponse)

    @get("/")
    async def get_agents(
        self,
        agent_service: AgentService,
    ) -> service.OffsetPagination[AgentResponse]:
        objs = await agent_service.list()
        return agent_service.to_schema(objs, schema_type=AgentResponse)

    @put("/{agent_id:int}")
    async def update_agent(
        self,
        agent_id: int,
        data: AgentUpdate,
        agent_service: AgentService,
    ) -> AgentResponse:
        obj = await agent_service.update(data=data, item_id=agent_id)
        return agent_service.to_schema(obj, schema_type=AgentResponse)

    @delete("/{agent_id:int}", status_code=200)
    async def delete_agent(
        self,
        agent_id: int,
        agent_service: AgentService,
    ) -> AgentResponse:
        obj = await agent_service.delete(agent_id)
        return agent_service.to_schema(obj, schema_type=AgentResponse)
