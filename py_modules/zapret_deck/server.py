"""
Lightweight asynchronous HTTP/JSON API server for zapret-deck.
Enables communication between the Decky Loader backend and external tools,
such as the Desktop Mode System Tray widget.
"""

import os
import json
import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from zapret_deck.constants import IPC_HOST, IPC_PORT, IPC_SOCKET_PATH


class ZapretDeckApiServer:
    """Async HTTP daemon server for IPC control of Zapret and WARP."""

    def __init__(
        self,
        plugin_instance,
        logger=None,
        host: str = IPC_HOST,
        port: int = IPC_PORT,
        socket_path: str = IPC_SOCKET_PATH,
    ):
        self.plugin = plugin_instance
        self.logger = logger
        self.host = host
        self.port = port
        self.socket_path = socket_path
        self.tcp_server: Optional[asyncio.AbstractServer] = None
        self.unix_server: Optional[asyncio.AbstractServer] = None
        self._running = False

    def log(self, msg: str):
        if self.logger:
            self.logger.info(f"[API Server] {msg}")
        else:
            print(f"[API Server] {msg}")

    async def start(self) -> None:
        """Starts TCP and Unix domain socket listeners."""
        if self._running:
            return
        self._running = True

        # 1. Start TCP listener
        try:
            self.tcp_server = await asyncio.start_server(
                self._handle_client,
                host=self.host,
                port=self.port,
                reuse_address=True,
            )
            self.log(f"Listening on TCP http://{self.host}:{self.port}")
        except Exception as e:
            self.log(f"Failed to start TCP listener on {self.host}:{self.port}: {e}")

        # 2. Start Unix domain socket listener
        if self.socket_path:
            try:
                if os.path.exists(self.socket_path):
                    try:
                        os.remove(self.socket_path)
                    except Exception:
                        pass

                self.unix_server = await asyncio.start_unix_server(
                    self._handle_client,
                    path=self.socket_path,
                )
                try:
                    os.chmod(self.socket_path, 0o666)
                except Exception:
                    pass
                self.log(f"Listening on Unix socket {self.socket_path}")
            except Exception as e:
                self.log(f"Failed to start Unix socket listener: {e}")

    async def stop(self) -> None:
        """Stops listeners and cleans up socket files."""
        self._running = False
        if self.tcp_server:
            self.tcp_server.close()
            await self.tcp_server.wait_closed()
            self.tcp_server = None

        if self.unix_server:
            self.unix_server.close()
            await self.unix_server.wait_closed()
            self.unix_server = None

        if self.socket_path and os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except Exception:
                pass
        self.log("API Server stopped.")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Processes HTTP requests from clients."""
        try:
            header_data = bytearray()
            while True:
                line = await reader.readline()
                if not line:
                    break
                header_data.extend(line)
                if line == b"\r\n" or line == b"\n":
                    break
                if len(header_data) > 65536:
                    break

            if not header_data:
                writer.close()
                await writer.wait_closed()
                return

            header_text = header_data.decode("utf-8", errors="replace")
            lines = header_text.splitlines()
            if not lines:
                writer.close()
                await writer.wait_closed()
                return

            request_line = lines[0].strip()
            parts = request_line.split()
            if len(parts) < 2:
                writer.close()
                await writer.wait_closed()
                return

            method = parts[0].upper()
            raw_url = parts[1]
            parsed_url = urlparse(raw_url)
            path = parsed_url.path

            headers = {}
            for h in lines[1:]:
                if ":" in h:
                    k, v = h.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

            content_length = int(headers.get("content-length", 0))

            body_bytes = b""
            if content_length > 0:
                body_bytes = await reader.readexactly(content_length)

            if method == "OPTIONS":
                await self._send_cors_response(writer)
                return

            body_data = {}
            if body_bytes:
                try:
                    body_data = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    body_data = {}

            status_code, response_data = await self._route_request(
                method, path, body_data
            )
            await self._send_json_response(writer, status_code, response_data)

        except Exception as e:
            try:
                await self._send_json_response(writer, 500, {"error": str(e)})
            except Exception:
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _route_request(
        self, method: str, path: str, data: Dict[str, Any]
    ) -> tuple:
        """Dispatches request to appropriate plugin method."""

        # ── GET /api/status ──
        if method == "GET" and path == "/api/status":
            raw_status = await self.plugin.get_status()
            status = dict(raw_status) if isinstance(raw_status, dict) else {}
            status["version"] = "1.1.1"
            return 200, status

        # ── GET /api/strategies ──
        if method == "GET" and path == "/api/strategies":
            strategies = await self.plugin.get_strategies()
            return 200, {"strategies": strategies}

        # ── POST /api/service ──
        if method == "POST" and path == "/api/service":
            service = data.get("service")
            enabled = bool(data.get("enabled", True))
            if service not in ["zapret", "warp"]:
                return 400, {"error": f"Invalid service: {service}"}
            res = await self.plugin.set_service_state(service, enabled)
            return 200, res

        # ── POST /api/strategy ──
        if method == "POST" and path == "/api/strategy":
            strategy = data.get("strategy", "")
            res = await self.plugin.apply_strategy(strategy)
            return 200, res

        # ── POST /api/autotune ──
        if method == "POST" and path == "/api/autotune":
            res = await self.plugin.start_autotune()
            return 200, res

        # ── POST /api/generate_warp ──
        if method == "POST" and path == "/api/generate_warp":
            res = await self.plugin.generate_warp()
            return 200, res

        # ── GET /api/desktop/status ──
        if method == "GET" and path == "/api/desktop/status":
            from tray.desktop_integration import get_desktop_integration_status
            plugin_dir = getattr(self.plugin, "plugin_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            status = get_desktop_integration_status(plugin_dir)
            settings = getattr(self.plugin, "settings", {})
            status["enabled"] = settings.get("desktop_tray_enabled", True)
            return 200, status

        # ── POST /api/desktop/autostart ──
        if method == "POST" and path == "/api/desktop/autostart":
            enable = bool(data.get("enable", True))
            from tray.desktop_integration import set_autostart
            plugin_dir = getattr(self.plugin, "plugin_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            success = set_autostart(plugin_dir, enable)
            if hasattr(self.plugin, "settings"):
                self.plugin.settings["desktop_tray_enabled"] = enable
                if hasattr(self.plugin, "save_settings"):
                    self.plugin.save_settings()
            return 200, {"success": success, "autostart": enable}

        # ── POST /api/desktop/launch ──
        if method == "POST" and path == "/api/desktop/launch":
            from tray.desktop_integration import launch_tray_process
            plugin_dir = getattr(self.plugin, "plugin_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            success = launch_tray_process(plugin_dir)
            return 200, {"success": success}

        return 404, {"error": f"Endpoint not found: {method} {path}"}

    async def _send_cors_response(self, writer: asyncio.StreamWriter) -> None:
        """Responds to CORS preflight OPTIONS."""
        response = (
            b"HTTP/1.1 204 No Content\r\n"
            b"Access-Control-Allow-Origin: *\r\n"
            b"Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
            b"Access-Control-Allow-Headers: Content-Type\r\n"
            b"Connection: close\r\n\r\n"
        )
        writer.write(response)
        await writer.drain()

    async def _send_json_response(
        self, writer: asyncio.StreamWriter, status_code: int, data: Any
    ) -> None:
        """Sends an HTTP response with JSON payload."""
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        status_text = (
            "OK"
            if status_code == 200
            else ("Not Found" if status_code == 404 else "Error")
        )
        headers = (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("utf-8")

        writer.write(headers + payload)
        await writer.drain()
