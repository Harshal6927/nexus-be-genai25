# Nexus BE - GenAI Genesis

## Local Setup

> This project built using `Python 3.12.x`

### API Keys

You will need [GEMINI API](https://ai.google.dev/gemini-api/docs/api-key). Add these keys to the `.env` file. Refer to the `.env.example` file for the format.

### Database

```bash
docker compose up -d
```

### Environment

NOTE: You need to have [uv](https://docs.astral.sh/uv/) installed to run the following commands.

```bash
uv sync
```

Activate virutal environment

```bash
.venv\Scripts\activate # for windows
# or
source .venv/bin/activate # for linux
```

### Run the application

```bash
litestar run
```

### API Schema

You can find the API schema at the `/schema` endpoint.

```bash
http://localhost:8000/schema
```
