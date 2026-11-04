import asyncio
import json
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from research_manager import ResearchManager

load_dotenv(override=True)

BASE = Path(__file__).parent
security = HTTPBasic(auto_error=False)
limiter = asyncio.Semaphore(2)  # max concurrent research runs


def check_auth(creds: HTTPBasicCredentials | None = Depends(security)):
    """Optional password gate: active only when APP_PASSWORD is set (username: admin)."""
    pw = os.getenv("APP_PASSWORD")
    if not pw:
        return
    ok = (
        creds is not None
        and secrets.compare_digest(creds.username, "admin")
        and secrets.compare_digest(creds.password, pw)
    )
    if not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": 'Basic realm="Deep Research"'},
        )


app = FastAPI(title="Deep Research", dependencies=[Depends(check_auth)])


class ResearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)


@app.get("/")
async def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/api/research")
async def research(req: ResearchRequest):
    async def stream():
        if limiter.locked():
            yield json.dumps({"type": "error", "text": "Server busy, try again shortly."}) + "\n"
            return
        async with limiter:
            try:
                async for kind, text in ResearchManager().run(req.query):
                    yield json.dumps({"type": kind, "text": text}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "text": f"Research failed: {e}"}) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")
