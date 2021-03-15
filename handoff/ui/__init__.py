import logging, os
import uvicorn

import handoff
from handoff.config import (
    init_state,
    get_state,
    CLOUD_PROVIDER,
    CLOUD_PLATFORM,
    CONTAINER_PROVIDER,
)
from handoff.ui import backend

logger = logging.getLogger(__name__)


def server(port=8000, **kwargs):
    """
    init_state(stage="prod")
    state = get_state()
    state.set_env(STAGE, "prod")
    state.set_env(CLOUD_PROVIDER, "aws")
    state.set_env(CLOUD_PLATFORM, "fargate")
    state.set_env(CONTAINER_PROVIDER, "docker")
    """
    wd = os.getcwd()
    CODE_DIR, _ = os.path.split(__file__)
    logger.info(f"Current directory is {wd}")
    logger.info(f"Starting server at port {port}")
    uvicorn.run(
        "handoff.ui.backend.main:app",
        reload=True,
        reload_dirs=[CODE_DIR],
        host="127.0.0.1",
        port=port,
        log_level="info",
    )
