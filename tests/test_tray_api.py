"""
Test script for Zapret-Deck IPC API Server and API Client.
Verifies server lifecycle, endpoint responses, and client methods.
"""

import os
import sys
import asyncio
import unittest

# Ensure root dir and py_modules are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_MODULES = os.path.join(BASE_DIR, "py_modules")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PY_MODULES not in sys.path:
    sys.path.insert(0, PY_MODULES)

from zapret_deck.server import ZapretDeckApiServer
from tray.api_client import ZapretDeckApiClient
from tray.desktop_integration import get_desktop_paths, generate_autostart_content


class MockPlugin:
    def __init__(self):
        self.plugin_dir = BASE_DIR
        self.settings = {
            "zapret_enabled": False,
            "warp_enabled": False,
            "current_strategy": "--filter-tcp=443 --dpi-desync=split2",
            "desktop_tray_enabled": True,
        }
        self.autotune_in_progress = False

    async def get_status(self):
        return {
            "zapret_enabled": self.settings["zapret_enabled"],
            "warp_enabled": self.settings["warp_enabled"],
            "zapret_active": self.settings["zapret_enabled"],
            "warp_active": self.settings["warp_enabled"],
            "warp_registered": True,
            "autotune_in_progress": self.autotune_in_progress,
            "current_strategy": self.settings["current_strategy"],
            "current_strategy_name": "Test Strategy",
        }

    async def get_strategies(self):
        return [
            {"name": "General (split2)", "args": "--filter-tcp=443 --dpi-desync=split2"},
            {"name": "Discord & Youtube (fake)", "args": "--filter-tcp=443 --dpi-desync=fake"},
        ]

    async def set_service_state(self, service: str, enabled: bool):
        self.settings[f"{service}_enabled"] = enabled
        return {"success": True, "service": service, "enabled": enabled}

    async def apply_strategy(self, strategy: str):
        self.settings["current_strategy"] = strategy
        return {"success": True, "strategy": strategy}

    async def start_autotune(self):
        self.autotune_in_progress = True
        return {"success": True}

    async def generate_warp(self):
        return {"success": True}


class TestZapretDeckApi(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.plugin = MockPlugin()
        self.test_port = 45998
        self.server = ZapretDeckApiServer(
            self.plugin, host="127.0.0.1", port=self.test_port, socket_path=None
        )
        await self.server.start()
        self.client = ZapretDeckApiClient(host="127.0.0.1", port=self.test_port)

    async def asyncTearDown(self):
        await self.server.stop()

    async def test_daemon_status(self):
        status = await asyncio.to_thread(self.client.get_status)
        self.assertIsNotNone(status)
        self.assertFalse(status.get("zapret_enabled"))
        self.assertEqual(status.get("current_strategy_name"), "Test Strategy")
        self.assertEqual(status.get("version"), "1.1.1")

    async def test_daemon_strategies(self):
        strategies = await asyncio.to_thread(self.client.get_strategies)
        self.assertEqual(len(strategies), 2)
        self.assertEqual(strategies[0]["name"], "General (split2)")

    async def test_daemon_service_toggle(self):
        res = await asyncio.to_thread(self.client.set_service_state, "zapret", True)
        self.assertTrue(res)
        status = await asyncio.to_thread(self.client.get_status)
        self.assertTrue(status.get("zapret_enabled"))

        res = await asyncio.to_thread(self.client.set_service_state, "zapret", False)
        self.assertTrue(res)
        status = await asyncio.to_thread(self.client.get_status)
        self.assertFalse(status.get("zapret_enabled"))

    async def test_daemon_strategy_apply(self):
        new_strat = "--filter-tcp=443 --dpi-desync=fake"
        res = await asyncio.to_thread(self.client.apply_strategy, new_strat)
        self.assertTrue(res)
        status = await asyncio.to_thread(self.client.get_status)
        self.assertEqual(status.get("current_strategy"), new_strat)

    async def test_daemon_autotune_and_warp(self):
        res_at = await asyncio.to_thread(self.client.start_autotune)
        self.assertTrue(res_at)
        status = await asyncio.to_thread(self.client.get_status)
        self.assertTrue(status.get("autotune_in_progress"))

        res_warp = await asyncio.to_thread(self.client.generate_warp)
        self.assertTrue(res_warp)

    def test_autostart_generation(self):
        content = generate_autostart_content(BASE_DIR)
        self.assertIn("Name=Zapret Deck Tray", content)
        self.assertIn("NoDisplay=true", content)
        self.assertIn("Exec=python3", content)
        self.assertIn("tray/tray_app.py", content)
        self.assertIn("assets/logo.png", content)


if __name__ == "__main__":
    unittest.main()
