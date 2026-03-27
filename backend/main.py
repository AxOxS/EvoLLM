"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from backend.database import engine, Base
from backend.routers import user, task, rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    Base.metadata.create_all(bind=engine)

    # Migrate: add missing columns for existing DBs
    inspector = inspect(engine)
    if inspector.has_table("tasks"):
        columns = [c["name"] for c in inspector.get_columns("tasks")]
        with engine.connect() as conn:
            if "conversation_id" not in columns:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN conversation_id VARCHAR(12)"))
            if "title" not in columns:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN title VARCHAR(255)"))
            # Clean up stale tasks from previous runs (Docker restart etc.)
            conn.execute(text(
                "UPDATE tasks SET status = 'failed', result = 'Interrupted by server restart.' "
                "WHERE status IN ('pending', 'in_progress')"
            ))
            conn.commit()

    yield


app = FastAPI(title="EvoLLM API", version="1.0.0", lifespan=lifespan)

# CORS – allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(task.router)
app.include_router(rag.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
