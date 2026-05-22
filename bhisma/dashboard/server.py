"""
Dashboard Server
================
FastAPI + WebSocket server for the Bhisma web dashboard.
"""

import os
import json
import webbrowser
from typing import Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from bhisma.dashboard.websocket import DashboardWebsocket
from bhisma.utils.constants import FRAMEWORK_NAME, FRAMEWORK_VERSION

# Determine paths
def _get_module_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(_get_module_dir(), "static")
TEMPLATES_DIR = os.path.join(_get_module_dir(), "templates")

# Create FastAPI app
app = FastAPI(
    title=f"{FRAMEWORK_NAME} Dashboard",
    description=f"{FRAMEWORK_NAME} v{FRAMEWORK_VERSION} Web Dashboard",
    version=FRAMEWORK_VERSION,
)

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# WebSocket manager
ws_manager = DashboardWebsocket()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "framework_name": FRAMEWORK_NAME,
        "version": FRAMEWORK_VERSION,
    })


@app.get("/api/status")
async def api_status():
    """Return framework status."""
    return {
        "framework": FRAMEWORK_NAME,
        "version": FRAMEWORK_VERSION,
        "status": "running",
        "active_connections": ws_manager.connection_count(),
    }


@app.get("/api/targets")
async def api_targets():
    """Return discovered targets."""
    # Placeholder — would integrate with recon module
    return {"targets": []}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "status_request":
                    # Send real system status
                    status = await get_system_status()
                    await ws_manager.send_personal_message(websocket, {"type": "status", "data": status})
            except json.JSONDecodeError:
                await ws_manager.send_personal_message(websocket, {"echo": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


async def get_system_status() -> Dict[str, Any]:
    """Collect real system status."""
    import psutil
    from bhisma.brain.orchestrator import LLMOrchestrator
    from bhisma.core.config import BhismaConfig
    from bhisma.utils.platform import PLATFORM

    status = {
        "iface": PLATFORM.detect_adapters()[0]["name"] if PLATFORM.detect_adapters() else "--",
        "monitor": True,  # Would check actual monitor mode
        "cpu": psutil.cpu_percent(interval=0.1),
        "mem": f"{psutil.virtual_memory().percent}%",
        "providers": {},
    }

    # Check AI provider status
    try:
        config = BhismaConfig.load()
        ai = LLMOrchestrator(config)
        for provider in ai.get_active_providers():
            status["providers"][provider] = "ok"
    except Exception:
        pass

    return status


def start_dashboard(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
    """Start the uvicorn server and optionally open browser."""
    import uvicorn
    if open_browser:
        url = f"http://{host}:{port}"
        # Delay slightly to let server start
        import threading
        def open_browser_delayed():
            import time
            time.sleep(1.5)
            webbrowser.open(url)
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")
