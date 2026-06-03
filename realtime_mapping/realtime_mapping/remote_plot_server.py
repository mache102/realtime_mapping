"""Remote plot server using FastAPI + WebSockets.

Provides a lightweight web server that streams heatmap data to
browser-based clients over WebSocket. Designed for LAN use where
a phone/tablet views the live plot from a ROS laptop.
"""

import asyncio
import json
import threading
import socket
import os
from typing import Optional, Set, Dict, Any

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn


class RemotePlotServer:
    """WebSocket server that broadcasts heatmap data to browser clients."""

    def __init__(self, port: int = 8090, static_dir: Optional[str] = None):
        self.port = port
        self.static_dir = static_dir
        self.clients: Set[WebSocket] = set()
        self.latest_data: Optional[Dict[str, Any]] = None
        self.lock = threading.Lock()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure FastAPI routes."""

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            self.clients.add(websocket)
            try:
                with self.lock:
                    if self.latest_data is not None:
                        await websocket.send_json(self.latest_data)
                while True:
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text("pong")
            except WebSocketDisconnect:
                pass
            except Exception:
                pass
            finally:
                self.clients.discard(websocket)

        if self.static_dir and os.path.isdir(self.static_dir):
            self.app.mount(
                "/",
                StaticFiles(directory=self.static_dir, html=True),
                name="static",
            )

    def update_and_broadcast(
        self,
        heatmap_values: np.ndarray,
        heatmap_counts: np.ndarray,
        positions: list,
        extent: list,
        sensor_range: dict,
    ) -> None:
        """Thread-safe update of heatmap data and broadcast to all clients.

        Called from the ROS thread. Schedules the broadcast coroutine
        on the server's event loop.
        """
        data = {
            "type": "heatmap_update",
            "heatmap_values": (
                heatmap_values.tolist()
                if isinstance(heatmap_values, np.ndarray)
                else heatmap_values
            ),
            "heatmap_counts": (
                heatmap_counts.tolist()
                if isinstance(heatmap_counts, np.ndarray)
                else heatmap_counts
            ),
            "positions": positions,
            "extent": extent,
            "sensor_range": sensor_range,
        }

        with self.lock:
            self.latest_data = data

        if self.loop is not None and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast(data), self.loop)

    async def _broadcast(self, data: Dict[str, Any]) -> None:
        """Send data to all connected clients, removing dead connections."""
        disconnected: Set[WebSocket] = set()
        for client in self.clients:
            try:
                await client.send_json(data)
            except Exception:
                disconnected.add(client)
        self.clients -= disconnected


    def run(self) -> None:
        """Run the FastAPI server."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop

        # --- ADD THIS LOGGING BLOCK ---
        real_ip = get_lan_ip()
        print("\n" + "="*50)
        print(f"🚀 SERVER LIVE! Access the remote plot at:")
        print(f"👉 Local (this machine): http://127.0.0.1:{self.port}")
        print(f"👉 LAN (Phone/Tablet):   http://{real_ip}:{self.port}")
        print("="*50 + "\n")
        # ------------------------------

        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())


def get_lan_ip() -> str:
    """Return the LAN IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except OSError:
        try:
            s.connect(("192.168.255.255", 1))
            ip = s.getsockname()[0]
        except OSError:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def resolve_static_dir(static_dir: Optional[str]) -> Optional[str]:
    """Resolve the static directory for serving the frontend.

    Checks, in order:
    1. Explicit path passed by the user.
    2. ``remote-plot/dist`` relative to the current working directory.
    3. ``../remote-plot/dist`` relative to this file (repo root layout).
    """
    if static_dir and os.path.isdir(static_dir):
        return os.path.abspath(static_dir)

    cwd_candidate = os.path.join(os.getcwd(), "remote-plot", "dist")
    if os.path.isdir(cwd_candidate):
        return cwd_candidate

    file_candidate = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "remote-plot", "dist",
    )
    file_candidate = os.path.normpath(file_candidate)
    if os.path.isdir(file_candidate):
        return file_candidate

    return None
