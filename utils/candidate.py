from saq.types import Context
from sqlalchemy import select

from config import DB_CONFIG
from models import Candidate


async def process_candidate(_: Context) -> None:
    # process the candidate

    async with DB_CONFIG.get_session() as transaction:
        candidate = await transaction.scalars(select(Candidate))
        print(list(candidate))
