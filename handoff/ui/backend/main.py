import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models, database, config
from .routers import core, handoff

models.Base.metadata.create_all(bind=database.engine)

CODE_DIR, _ = os.path.split(__file__)
FRONTEND_DIR = os.path.join(CODE_DIR, "../frontend")

app = FastAPI()
app.include_router(core.router)
app.include_router(handoff.router)
app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_DIR + "/assets"),
    name="static")

app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)
