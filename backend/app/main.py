from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import applications, auth, publications, users
from app.core.config import settings


app = FastAPI(title="Business Club API")


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if settings.frontend_url not in origins:
    origins.append(settings.frontend_url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(publications.router)
app.include_router(applications.router)


@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }

