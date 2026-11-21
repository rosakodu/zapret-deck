"""
HTTP Client for communication with Zapret-Deck local IPC API daemon.
Handles REST requests with fail-safe error handling and timeouts.
"""

import os
import sys
import json
import http.client
import socket
from typing import Dict, List, Any, Optional

# Ensure plugin root and py_modules are accessible
_script_dir = os.path.dirname(os.path.abspath(__file__))
_plugin_dir = os.path.dirname(_script_dir)
_py_modules = os.path.join(_plugin_dir, "py_modules")
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)
if _py_modules not in sys.path:
    sys.path.insert(0, _py_modules)

from zapret_deck.constants import IPC_SOCKET_PATH


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str, timeout: float):
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


class ZapretDeckApiClient:
    """Client for local zapret-deck daemon."""

    def __init__(self, socket_path: str = IPC_SOCKET_PATH, timeout: float = 8.0):
        self.socket_path = socket_path
        self.timeout = timeout

    def _request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        headers = {}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        connection = UnixHTTPConnection(self.socket_path, self.timeout)
        try:
            connection.request(method, f"/api{endpoint}", body=body, headers=headers)
            with connection.getresponse() as response:
                if response.status == 200:
                    return json.loads(response.read())
        except (OSError, http.client.HTTPException, ValueError):
            return None
        finally:
            connection.close()

    def is_available(self) -> bool:
        """Checks whether the daemon is actively responding."""
        res = self._request("GET", "/status")
        return res is not None

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Fetches current Zapret & WARP state, strategy, and autotune status."""
        return self._request("GET", "/status")

    def get_strategies(self) -> List[Dict[str, Any]]:
        """Fetches available strategies."""
        res = self._request("GET", "/strategies")
        if res and "strategies" in res and isinstance(res["strategies"], list):
            return res["strategies"]
        return []

    def set_service_state(self, service: str, enabled: bool) -> bool:
        """Enables or disables service ('zapret' or 'warp')."""
        res = self._request("POST", "/service", {"service": service, "enabled": enabled})
        return bool(res and res.get("success"))

    def apply_strategy(self, strategy: str) -> bool:
        """Applies a selected Zapret strategy."""
        res = self._request("POST", "/strategy", {"strategy": strategy})
        return bool(res and res.get("success"))

    def start_autotune(self) -> bool:
        """Starts automated strategy detection."""
        res = self._request("POST", "/autotune")
        return bool(res and res.get("success"))

    def generate_warp(self) -> bool:
        """Generates a new WARP account."""
        res = self._request("POST", "/generate_warp")
        return bool(res and res.get("success"))

    def get_desktop_status(self) -> Dict[str, Any]:
        """Checks autostart and desktop installation status."""
        res = self._request("GET", "/desktop/status")
        return res or {"autostart": False, "enabled": False}

    def set_autostart(self, enable: bool) -> bool:
        """Toggles desktop autostart."""
        res = self._request("POST", "/desktop/autostart", {"enable": enable})
        return bool(res and res.get("success"))
