from fastapi import FastAPI
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.publications import router as publications_router
from app.api.applications import router as applications_router
from app.db.session import engine

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Business Club Startups API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(publications_router)
app.include_router(applications_router)


@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }

