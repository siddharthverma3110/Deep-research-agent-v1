# Deep Research Agent

Planner -> parallel Search agents (OpenAI WebSearchTool) -> Writer.
Served by FastAPI with a single static HTML page (no Gradio).

## Run locally
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # add OPENAI_API_KEY
    uvicorn app:app --reload --port 8000
Open http://localhost:8000

## Deploy on Render
1. Push this folder to GitHub (.env is git-ignored).
2. Render Dashboard > New > Blueprint > select the repo.
3. Enter OPENAI_API_KEY and APP_PASSWORD (username: admin) when prompted.
4. Open the generated https://<name>.onrender.com URL.

## Academic search keys
Academic papers come from OpenAlex, which now requires a free API key (openalex.org/settings/api).
Set OPENALEX_API_KEY (locally in .env, on Render under Environment). Without a key, academic search is disabled and that report section will be empty.
Search failures are written to the logs (Render: your service > Logs).
