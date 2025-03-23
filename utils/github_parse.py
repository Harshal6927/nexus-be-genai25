import base64
from datetime import datetime, timedelta
from typing import Any

import httpx

# Replace with your GitHub username and Personal Access Token (if needed)
from config import GITHUB_TOKEN

BASE_URL = "https://api.github.com"


async def get_user_repos(username: str, token=None) -> Any | None:
    url = f"{BASE_URL}/users/{username}/repos?sort=created&direction=desc&per_page=10"

    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()


async def get_readme(owner: str, repo: str, token: str | None = None) -> tuple[Any, None] | tuple[None, str]:
    url = f"{BASE_URL}/repos/{owner}/{repo}/readme"
    headers = {"Authorization": f"token {token}"} if token else {}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json(), None
        error = f"  Failed to fetch README for {owner}/{repo}. Status: {response.status_code}"
        return None, error


async def generate_repo_info(repos, token: str | None = None) -> str:
    repo_info = ""
    if repos:
        for repo in repos:
            repo_info += f"\nProject Name: {repo['name']}\n"
            repo_info += f"Main Programming Language: {repo['language']}\n"
            repo_info += f"Description: {repo['description']}\n"

            # README
            readme, error = await get_readme(repo["owner"]["login"], repo["name"], token)
            if readme:
                try:
                    content = base64.b64decode(readme["content"]).decode("utf-8")
                    if len(content) > 3500:
                        content = content[:3500] + "..."
                    repo_info += f"\nREADME Content:\n{content}\n"
                except Exception as e:
                    repo_info += f"\nError decoding README: {e!s}\n"
            elif error:
                repo_info += f"{error}\n"
            else:
                repo_info += "\nNo README found\n"
            repo_info += "-" * 40 + "\n"
    return repo_info


async def get_commit_count_for_repo(owner, repo, username, since_date, token=None) -> tuple[int, str | None]:
    url = f"{BASE_URL}/repos/{owner}/{repo}/commits"
    headers = {"Authorization": f"token {token}"} if token else {}
    params = {
        "author": username,
        "since": since_date.isoformat(),
        "per_page": 100,
    }
    total = 0
    error = None

    async with httpx.AsyncClient() as client:
        while url:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                commits = response.json()
                total += len(commits)
                # Extract next page URL from Link header if it exists
                next_link = response.headers.get("link")
                if next_link and 'rel="next"' in next_link:
                    # Extract URL between < and >
                    url = next_link.split("<")[1].split(">")[0]
                else:
                    url = None
                params = {}
            else:
                error = f"  Error fetching commits for {owner}/{repo}: {response.status_code}"
                break
        return total, error


async def process_github(username: str) -> str:
    output = ""

    repos = await get_user_repos(username, GITHUB_TOKEN)

    if repos:
        repo_info = await generate_repo_info(repos, GITHUB_TOKEN)
        output += repo_info

        since_date = datetime.now() - timedelta(days=365)
        total_commits = 0

        output += "\nCalculating commit history...\n"
        for repo in repos:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            checking_msg = f"  Checking {repo_name}... "
            count, commit_error = await get_commit_count_for_repo(owner, repo_name, username, since_date, GITHUB_TOKEN)
            total_commits += count
            if commit_error:
                checking_msg += commit_error
            else:
                checking_msg += f"found {count} commits"
            output += checking_msg + "\n"

        output += "\n" + "=" * 50 + "\n"
        output += f"Total commits by {username} in the past year: {total_commits}\n"
        output += "=" * 50 + "\n"
    else:
        output += "No repositories found or error occurred.\n"

    return output
