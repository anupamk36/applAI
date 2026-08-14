from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    answer_bank,
    auth,
    facts,
    field_resolution,
    jobs,
    matching,
    resumes,
    settings,
)

app = FastAPI(title="ApplAI core-api", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(facts.router)
app.include_router(jobs.router)
app.include_router(settings.router)
app.include_router(answer_bank.router)
app.include_router(matching.router)
app.include_router(field_resolution.router)


@app.get("/health")
def health():
    return {"status": "ok"}
