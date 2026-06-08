from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import OUTPUT_DIR, TEMP_DIR
from app.routers import render
from app.utils.structured_log import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="COUNTDOWN Video Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(render.router)
