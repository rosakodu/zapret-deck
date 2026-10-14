"""
HTTP Client for communication with Zapret-Deck local IPC API daemon.
Handles REST requests with fail-safe error handling and timeouts.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

# Ensure plugin root and py_modules are accessible
_script_dir = os.path.dirname(os.path.abspath(__file__))
_plugin_dir = os.path.dirname(_script_dir)
_py_modules = os.path.join(_plugin_dir, "py_modules")
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)
if _py_modules not in sys.path:
    sys.path.insert(0, _py_modules)

try:
    from zapret_deck.constants import IPC_HOST, IPC_PORT
except ImportError:
    IPC_HOST = "127.0.0.1"
    IPC_PORT = 45322


class ZapretDeckApiClient:
    """Client for local zapret-deck daemon."""

    def __init__(
        self, host: str = IPC_HOST, port: int = IPC_PORT, timeout: float = 3.0
    ):
        self.base_url = f"http://{host}:{port}/api"
        self.timeout = timeout

    def _request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Performs HTTP request to the local daemon."""
        url = f"{self.base_url}{endpoint}"
        body_bytes = None
        headers = {"User-Agent": "ZapretDeck-Tray/1.0"}

        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        req = urllib.request.Request(
            url, data=body_bytes, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_data = resp.read().decode("utf-8", errors="replace")
                if resp_data:
                    return json.loads(resp_data)
                return {}
        except Exception:
            return None

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
