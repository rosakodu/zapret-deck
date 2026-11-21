"""
Lightweight asynchronous HTTP/JSON API server for zapret-deck.
Enables communication between the Decky Loader backend and external tools,
such as the Desktop Mode System Tray widget.
"""

import os
import json
import socket
import stat
import struct
import asyncio
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from zapret_deck.constants import IPC_SOCKET_PATH


class ZapretDeckApiServer:
    """Async HTTP daemon server for IPC control of Zapret and WARP."""

    def __init__(
        self,
        plugin_instance,
        logger=None,
        socket_path: str = IPC_SOCKET_PATH,
        *,
        allowed_uid: int,
    ):
        self.plugin = plugin_instance
        self.logger = logger
        self.socket_path = socket_path
        self.allowed_uid = allowed_uid
        manifest = Path(plugin_instance.plugin_dir) / "plugin.json"
        with manifest.open(encoding="utf-8") as file:
            self.version = json.load(file)["version"]
        self.unix_server = None

    def log(self, msg: str):
        if self.logger:
            self.logger.info(f"[API Server] {msg}")
        else:
            print(f"[API Server] {msg}")

    async def start(self) -> None:
        """Listen on a Unix socket inside a directory controlled by the backend."""
        if self.unix_server is not None:
            return

        directory = os.path.dirname(self.socket_path)
        os.makedirs(directory, mode=0o755, exist_ok=True)
        info = os.lstat(directory)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_mode & 0o022):
            raise PermissionError(f"Unsafe IPC directory: {directory}")

        if os.path.lexists(self.socket_path):
            if not stat.S_ISSOCK(os.lstat(self.socket_path).st_mode):
                raise PermissionError(f"Unexpected file at {self.socket_path}")
            os.unlink(self.socket_path)

        server = await asyncio.start_unix_server(
            self._handle_client, path=self.socket_path, start_serving=False
        )
        try:
            os.chmod(self.socket_path, 0o600)
            os.chown(self.socket_path, self.allowed_uid, -1)
            await server.start_serving()
        except BaseException:
            server.close()
            await server.wait_closed()
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            raise
        self.unix_server = server
        self.log(f"Listening on Unix socket {self.socket_path}")

    async def stop(self) -> None:
        if self.unix_server is None:
            return
        self.unix_server.close()
        await self.unix_server.wait_closed()
        self.unix_server = None
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        self.log("API Server stopped.")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Processes HTTP requests from clients."""
        try:
            peer = writer.get_extra_info("socket")
            credentials = peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
            _, uid, _ = struct.unpack("3i", credentials)
            if uid != self.allowed_uid:
                await self._send_json_response(writer, 403, {"error": "Access denied"})
                return

            header_data = bytearray()
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=3)
                if not line:
                    break
                header_data.extend(line)
                if line == b"\r\n" or line == b"\n":
                    break
                if len(header_data) > 65536:
                    await self._send_json_response(writer, 400, {"error": "Headers too large"})
                    return

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

            if not 0 <= content_length <= 1024 * 1024:
                await self._send_json_response(writer, 400, {"error": "Invalid body size"})
                return

            body_data = {}
            if content_length:
                body_bytes = await asyncio.wait_for(reader.readexactly(content_length), timeout=3)
                try:
                    body_data = json.loads(body_bytes)
                except (ValueError, UnicodeError):
                    body_data = None
                if not isinstance(body_data, dict):
                    await self._send_json_response(writer, 400, {"error": "Expected a JSON object"})
                    return

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
            status["version"] = self.version
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
            f"Connection: close\r\n\r\n"
        ).encode("utf-8")

        writer.write(headers + payload)
        await writer.drain()
