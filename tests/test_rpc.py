"""
Tests for newly added RPC methods in main.py:
- start_ttl_tune
- get_available_fakes
- set_active_fake
- parse_bat_strategy
- _run_autotune integration
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure root dir and py_modules are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_MODULES = os.path.join(BASE_DIR, "py_modules")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PY_MODULES not in sys.path:
    sys.path.insert(0, PY_MODULES)

import main


class TestRpcMethods(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plugin_dir = self.temp_dir.name
        self.settings_dir = os.path.join(self.plugin_dir, ".config", "zapret-deck")
        os.makedirs(self.settings_dir, exist_ok=True)
        os.makedirs(os.path.join(self.plugin_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(self.plugin_dir, "lists"), exist_ok=True)

        # Mock decky logger
        main.decky = MagicMock()
        main.SETTINGS_DIR = self.settings_dir
        main.SETTINGS_FILE = os.path.join(self.settings_dir, "settings.json")
        main.HOSTLIST_FILE = os.path.join(self.settings_dir, "hostlist.txt")
        main.CUSTOM_STRATEGIES_FILE = os.path.join(self.settings_dir, "custom_strategies.json")

        self.plugin = main.Plugin()
        self.plugin.plugin_dir = self.plugin_dir
        self.plugin.zapret_manager.plugin_dir = self.plugin_dir
        self.plugin.zapret_manager.shared_dir = os.path.join(self.plugin_dir, "shared")
        self.plugin.zapret_manager.fakes_manager.bin_dir = os.path.join(self.plugin_dir, "bin")

        # Create a sample fake
        with open(os.path.join(self.plugin_dir, "bin", "quic_sample.bin"), "wb") as f:
            f.write(b"SAMPLE_QUIC_DATA")

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    async def test_failed_service_start_does_not_persist_enabled(self):
        with patch.object(self.plugin.zapret_manager, "start", side_effect=RuntimeError("queue busy")):
            result = await self.plugin.set_service_state("zapret", True)
        self.assertFalse(result["success"])
        self.assertIn("queue busy", result["error"])
        self.assertFalse(self.plugin.settings["zapret_enabled"])

    async def test_tray_api_starts_when_saved_zapret_state_cannot_be_restored(self):
        self.plugin.settings.update(zapret_enabled=True, desktop_tray_enabled=False)
        with (
            patch("main.os.geteuid", return_value=1000),
            patch("main.ZapretDeckApiServer") as api,
            patch.object(self.plugin.warp_manager, "cleanup_network"),
            patch.object(self.plugin.zapret_manager, "destroy_nftables"),
            patch.object(self.plugin.zapret_manager, "start", side_effect=RuntimeError("queue busy")),
        ):
            api.return_value.start = AsyncMock()
            await self.plugin._main()
            api.return_value.start.assert_awaited_once()
        self.assertFalse(self.plugin.settings["zapret_enabled"])

    async def test_failed_strategy_change_restores_previous_strategy(self):
        previous = self.plugin.settings["current_strategy"]
        self.plugin.settings["zapret_enabled"] = True
        with (
            patch.object(self.plugin.zapret_manager, "start", side_effect=[RuntimeError("failed"), None]) as start,
            patch.object(self.plugin.zapret_manager, "is_running", return_value=False),
        ):
            result = await self.plugin.apply_strategy("--filter-tcp=443")
        self.assertFalse(result["success"])
        self.assertTrue(self.plugin.settings["zapret_enabled"])
        self.assertEqual(self.plugin.settings["current_strategy"], previous)
        start.assert_called_with(previous, main.HOSTLIST_FILE)

    async def test_get_available_fakes(self):
        res = await self.plugin.get_available_fakes()
        self.assertTrue(res["success"])
        self.assertIn("fakes", res)
        self.assertIn("active_fake", res)
        fake_names = [f["name"] for f in res["fakes"]]
        self.assertIn("quic_sample.bin", fake_names)

    async def test_set_active_fake(self):
        res = await self.plugin.set_active_fake("quic_sample.bin")
        self.assertTrue(res["success"])
        self.assertEqual(res["active_fake"], "quic_sample.bin")

        # Verify active fake file exists
        active_path = os.path.join(self.plugin_dir, "bin", "ACTIVE_DISCORD_UDP.bin")
        self.assertTrue(os.path.isfile(active_path))

    async def test_parse_bat_strategy(self):
        bat = """@echo off
start "zapret" /min "%BIN%winws.exe" ^
--wf-tcp=80,443,2053 --wf-udp=443,50000-50100 ^
--filter-tcp=80,443 --dpi-desync=fake
"""
        res = await self.plugin.parse_bat_strategy(bat, name="TestBat")
        self.assertTrue(res["success"])
        strategy = res["strategy"]
        self.assertEqual(strategy["tcp_ports"], "80,443,2053")
        self.assertEqual(strategy["udp_ports"], "443,50000-50100")
        self.assertIn("--filter-tcp=80,443", strategy["clean_args"])
        self.assertNotIn("--wf-tcp", strategy["clean_args"])

    @patch("zapret_deck.autotune.AutotuneManager.tune_ttl_async")
    async def test_start_ttl_tune(self, mock_tune_async):
        mock_tune_async.return_value = {
            "success": True,
            "best_ttl": 6,
            "best_strategy_args": "--filter-tcp=80,443 --dpi-desync=fake --dpi-desync-ttl=6",
            "best_success_rate": 1.0,
            "best_latency_ms": 42.5,
            "results_by_ttl": {},
        }

        res = await self.plugin.start_ttl_tune(strategy_args="--dpi-desync=fake", ttl_min=1, ttl_max=10)
        self.assertTrue(res["success"])
        self.assertEqual(res["best_ttl"], 6)
        self.assertIn("--dpi-desync-ttl=6", res["best_strategy_args"])
        self.assertEqual(res["best_latency_ms"], 42.5)

    @patch("zapret_deck.autotune.AutotuneManager.rank_strategies_async")
    async def test_run_autotune_integration(self, mock_rank_async):
        mock_rank_async.return_value = [
            {
                "name": "Winning Strategy",
                "args": "--filter-tcp=80,443 --dpi-desync=multisplit",
                "success": True,
                "success_rate": 1.0,
                "avg_latency_ms": 38.0,
            }
        ]

        with (
            patch.object(self.plugin.zapret_manager, "start") as mock_start,
            patch.object(self.plugin.warp_manager, "stop"),
        ):
            await self.plugin._run_autotune()
            self.assertTrue(self.plugin.settings.get("zapret_enabled"))
            self.assertEqual(self.plugin.settings.get("current_strategy"), "--filter-tcp=80,443 --dpi-desync=multisplit")
            self.assertEqual(self.plugin.settings.get("autotuned_strategy_name"), "Winning Strategy")
            mock_start.assert_called()

    @patch("main.run_system_diagnostics")
    async def test_get_diagnostics_rpc(self, mock_diag):
        mock_diag.return_value = {
            "overall_ok": True,
            "kernel_modules": {"all_loaded": True},
            "nfqueue_220": {"is_busy": False},
            "dns_spoofing": {"has_spoofing": False, "results": []},
        }
        res = await self.plugin.get_diagnostics()
        self.assertTrue(res["success"])
        self.assertIn("diagnostics", res)
        self.assertTrue(res["diagnostics"]["overall_ok"])

    @patch("main.check_nfqueue_status")
    async def test_check_queue_status_rpc(self, mock_status):
        mock_status.return_value = {
            "queue_num": 220,
            "is_busy": False,
            "peer_port_id": None,
        }
        res = await self.plugin.check_queue_status()
        self.assertTrue(res["success"])
        self.assertIn("queue", res)
        self.assertFalse(res["queue"]["is_busy"])

    async def test_get_and_set_gamefilter_rpc(self):
        # 1. Проверяем получение конфига
        cfg_res = await self.plugin.get_gamefilter_config()
        self.assertTrue(cfg_res["success"])
        self.assertIn("config", cfg_res)
        self.assertTrue(cfg_res["config"]["enabled"])

        # 2. Выключаем GameFilter
        toggle_res = await self.plugin.set_gamefilter_enabled(False)
        self.assertTrue(toggle_res["success"])
        self.assertFalse(toggle_res["enabled"])
        self.assertFalse(self.plugin.zapret_manager.game_filter.is_enabled())
        self.assertFalse(self.plugin.settings.get("gamefilter_enabled"))

        # 3. Включаем обратно
        toggle_res2 = await self.plugin.set_gamefilter_enabled(True)
        self.assertTrue(toggle_res2["success"])
        self.assertTrue(toggle_res2["enabled"])
        self.assertTrue(self.plugin.zapret_manager.game_filter.is_enabled())
        self.assertTrue(self.plugin.settings.get("gamefilter_enabled"))

    @patch("zapret_deck.remote_fetcher.RemoteFetcher.sync")
    async def test_sync_remote_strategies_rpc(self, mock_sync):
        mock_sync.return_value = {
            "success": True,
            "count": 3,
            "downloaded_count": 3,
            "strategies": [{"name": "s1", "args": "--args1"}],
        }
        res = await self.plugin.sync_remote_strategies(repo="test/repo")
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 3)
        mock_sync.assert_called_once_with(repo="test/repo", branch=None, merge=True)


if __name__ == "__main__":
    unittest.main()
