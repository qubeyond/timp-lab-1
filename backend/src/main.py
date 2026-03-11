from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db
from src.api import router 
from src.settings import settings


@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    await init_db()
    yield


app = FastAPI(
    title="lab-1",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api/v1"
)


@app.get("/")
async def root():
    return {
        "message": "API is running",
        "docs": "/docs"
    }