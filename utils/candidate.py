from contextlib import suppress

import httpx
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from saq.types import Context
from sqlalchemy import select
from usp.tree import sitemap_tree_for_homepage

from config import DB_CONFIG, GENERATION_CONFIG, GOOGLE_GENAI
from models import Candidate

RUN_CONFIG = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
)


SYSTEM_INSTRUCTION_CHAT = "**SYSTEM:** You are an advanced HTML data processor. Your task is to analyze the provided HTML content and extract the candidates information. It is a portfolio website data. Extract the text content from the tags. Do not include HTML tags in the extracted text and only remove the Image or Href links. I want as much data as possibale. Generate output in Markdown"


async def process_portfolio(url: str) -> str:
    data = []
    tree = sitemap_tree_for_homepage(url).all_pages()

    async with AsyncWebCrawler() as crawler:
        for page in tree:
            result = await crawler.arun(
                url=page.url,
                config=RUN_CONFIG,
            )

            if result.success:
                data.append(f"URL: {page.url}\n HTML: {result.html}\n")

    return "\n".join(data)


async def process_candidate(_: Context) -> None:
    async with DB_CONFIG.get_session() as db_session:
        candidates = await db_session.scalars(select(Candidate).where(Candidate.data_processed == False))
        candidates = list(candidates)

    for candidate in candidates:
        model_chat = GOOGLE_GENAI.GenerativeModel(  # type: ignore
            model_name="gemini-1.5-flash-8b",
            generation_config=GENERATION_CONFIG,
            system_instruction=SYSTEM_INSTRUCTION_CHAT,
        )

        async with DB_CONFIG.get_session() as db_session:
            response = None
            if candidate.candidate_portfolio:
                candidate_portfolio_data = await process_portfolio(candidate.candidate_portfolio)
                chat_session = model_chat.start_chat()
                response = await chat_session.send_message_async(candidate_portfolio_data)
                response = response.text

            github = None
            if candidate.candidate_github:
                print("Processing Github")

            linkedin = None
            if candidate.candidate_linkedin:
                print("Processing Linkedin")

            resume = None
            if candidate.candidate_resume_id:
                print("Processing Resume")

            data = f"**RESUME:** {resume}\n\n\n\n**LINKEDIN:** {linkedin}\n\n\n\n**GITHUB:** {github}\n\n\n\n**PORTFOLIO:** {response}"

            # Skills
            system_instruction_skills = "**SYSTEM:** Your task is to analyze the provided candidate information and generate a valid python list of skills, for example: ['Python', 'Java', 'AWS', 'Docker', 'Kubernetes']. You can use the provided candidate information to generate the skills list.**SYSTEM:** Keep in mind that you can only reply with maximum 10 skills and do not add any extra information. Example: ['Python', 'Java', 'AWS', 'Docker', 'Kubernetes']. Do not do any formatting or add any special characters. Skills can be non-technical as well."

            model_skills = GOOGLE_GENAI.GenerativeModel(  # type: ignore
                model_name="gemini-1.5-flash-8b",
                generation_config=GENERATION_CONFIG,
                system_instruction=system_instruction_skills,
            )

            chat_session_skills = model_skills.start_chat()

            response_skills = await chat_session_skills.send_message_async(
                data,
            )

            skills = []
            if response_skills.text:
                with suppress(ValueError):
                    skills = eval(response_skills.text)

            # Summary
            system_instruction_summary = "**SYSTEM:** Your task is to analyze the provided candidate information and generate a summary of the candidate. You can use the provided candidate information to generate the summary.**SYSTEM:** Keep in mind that you can only reply with a summary of the candidate do not add any extra information. Example: 'Candidate is a Python Developer with 5 years of experience in Django and Flask, they are also contributing to open-source projects in their free time.'."

            model_summary = GOOGLE_GENAI.GenerativeModel(  # type: ignore
                model_name="gemini-1.5-flash-8b",
                generation_config=GENERATION_CONFIG,
                system_instruction=system_instruction_summary,
            )

            chat_session_summary = model_summary.start_chat()

            response_summary = await chat_session_summary.send_message_async(
                data,
            )

            summary = response_summary.text

            async with httpx.AsyncClient() as client:
                data = {
                    "data_processed": True,
                    "candidate_resume_data": resume,
                    "candidate_linkedin_data": linkedin,
                    "candidate_github_data": github,
                    "candidate_portfolio_data": response,
                }
                await client.put(f"http://127.0.0.1:8621/job-applications/candidate/{candidate.id}", json=data)

                job_application = await client.get(f"http://127.0.0.1:8621/job-applications/{candidate.id}")
                job_application = job_application.json()

                data = {
                    "candidate_skills": str(skills),
                    "candidate_summary": summary,
                }
                await client.put(f"http://127.0.0.1:8621/job-applications/{job_application['id']}", json=data)
