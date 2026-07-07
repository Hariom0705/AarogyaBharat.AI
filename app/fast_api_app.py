# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import asyncio
import contextlib
import os
from collections.abc import AsyncIterator

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.reasoning_engine_adapter import (
    attach_reasoning_engine_routes,
)
from app.app_utils.telemetry import (
    setup_agent_engine_telemetry,
    setup_telemetry,
)
from app.app_utils.typing import Feedback

load_dotenv()
setup_telemetry()
# Must run before get_fast_api_app to set the tracer provider resource.
setup_agent_engine_telemetry()
import logging

if os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "").lower() in ("true", "1"):
    try:
        _, project_id = google.auth.default()
        logging_client = google_cloud_logging.Client()
        logger = logging_client.logger(__name__)
        gcp_logging = True
    except Exception:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        gcp_logging = False
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    gcp_logging = False

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    import asyncio
    print("ACTIVE EVENT LOOP IN LIFESPAN:", type(asyncio.get_event_loop()))
    # Runner for the A2A path, sharing the same session/artifact services as the
    # adk_api and reasoning_engine paths (see services.py). Imported here so the
    # agent is built after env/telemetry setup.
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    # Shared by the A2A path and the reasoning_engine adapter routes.
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=os.path.join(AGENT_DIR, "app"),
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "aarogya-bharat"
app.description = "API for interacting with the Agent aarogya-bharat"


# Proxy routes so the Vertex AI Console Playground (reasoning_engine SDK) can
# talk to this agent alongside the native adk_api routes.
attach_reasoning_engine_routes(app)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/portal")
def get_portal():
    return FileResponse(os.path.join(AGENT_DIR, "app", "static", "index.html"))

# Create directory structure if not exist
os.makedirs(os.path.join(AGENT_DIR, "app", "static"), exist_ok=True)
app.mount("/portal/static", StaticFiles(directory=os.path.join(AGENT_DIR, "app", "static")), name="portal-static")

@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if gcp_logging:
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info(f"Feedback collected: {feedback.model_dump()}")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
