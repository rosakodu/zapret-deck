"""
Tests for autotune.py: TLS 1.3 testing, strategy ranking, and TTL tuning.
"""

import os
import sys
import socket
import unittest
from unittest.mock import patch, MagicMock

# Ensure root dir and py_modules are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_MODULES = os.path.join(BASE_DIR, "py_modules")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PY_MODULES not in sys.path:
    sys.path.insert(0, PY_MODULES)

from zapret_deck.autotune import (
    clean_host,
    inject_ttl,
    check_tls_handshake,
    test_connectivity,
    AutotuneManager,
    TLSCheckResult,
)


class TestAutotune(unittest.TestCase):
    def test_clean_host(self):
        self.assertEqual(clean_host("https://www.youtube.com/watch?v=1"), "www.youtube.com")
        self.assertEqual(clean_host("http://google.com"), "google.com")
        self.assertEqual(clean_host("discord.com:443"), "discord.com")
        self.assertEqual(clean_host("  gateway.discord.gg  "), "gateway.discord.gg")

    def test_inject_ttl(self):
        # 1. Single profile without existing TTL
        strat1 = "--filter-tcp=80,443 --dpi-desync=fake --dpi-desync-repeats=6"
        res1 = inject_ttl(strat1, 8)
        self.assertIn("--dpi-desync-ttl=8", res1)

        # 2. Strategy with existing TTL -> replace
        strat2 = "--filter-tcp=80,443 --dpi-desync=fake --dpi-desync-ttl=3 --dpi-desync-fooling=ts"
        res2 = inject_ttl(strat2, 12)
        self.assertIn("--dpi-desync-ttl=12", res2)
        self.assertNotIn("--dpi-desync-ttl=3", res2)

        # 3. Multi-profile with --new
        strat3 = (
            "--filter-tcp=80,443 --dpi-desync=fake --new "
            "--filter-udp=443 --dpi-desync=fake --dpi-desync-ttl=5"
        )
        res3 = inject_ttl(strat3, 10)
        tokens = res3.split()
        ttl_tokens = [t for t in tokens if t.startswith("--dpi-desync-ttl=")]
        self.assertEqual(len(ttl_tokens), 2)
        self.assertTrue(all(t == "--dpi-desync-ttl=10" for t in ttl_tokens))

        # 4. Clamping
        self.assertIn("--dpi-desync-ttl=1", inject_ttl(strat1, -5))
        self.assertIn("--dpi-desync-ttl=255", inject_ttl(strat1, 999))

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.socket")
    @patch("socket.getaddrinfo")
    def test_check_tls_handshake_mock_success(self, mock_getaddrinfo, mock_socket, mock_wrap):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("142.250.180.14", 443))
        ]
        mock_raw_sock = MagicMock()
        mock_socket.return_value = mock_raw_sock

        mock_ssock = MagicMock()
        mock_ssock.version.return_value = "TLSv1.3"
        mock_wrap.return_value.__enter__.return_value = mock_ssock

        res = check_tls_handshake("www.google.com")
        self.assertTrue(res.success)
        self.assertEqual(res.tls_version, "TLSv1.3")
        self.assertEqual(res.host, "www.google.com")
        self.assertGreaterEqual(res.latency_ms, 0.0)

    @patch("socket.socket")
    @patch("socket.getaddrinfo")
    def test_check_tls_handshake_mock_failure(self, mock_getaddrinfo, mock_socket):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("142.250.180.14", 443))
        ]
        mock_raw_sock = MagicMock()
        mock_raw_sock.connect.side_effect = TimeoutError("Connection timed out")
        mock_socket.return_value = mock_raw_sock

        res = check_tls_handshake("www.youtube.com")
        self.assertFalse(res.success)
        self.assertIn("timed out", res.error.lower())

    @patch("zapret_deck.autotune.check_tls_handshake")
    def test_test_connectivity(self, mock_check):
        def side_effect(host, **kwargs):
            if "youtube" in host:
                return TLSCheckResult(host=host, port=443, success=True, latency_ms=45.0, tls_version="TLSv1.3")
            return TLSCheckResult(host=host, port=443, success=False, latency_ms=100.0, error="RST")

        mock_check.side_effect = side_effect
        res = test_connectivity(["www.youtube.com", "discord.com"])
        self.assertTrue(res["success"])
        self.assertEqual(res["success_count"], 1)
        self.assertEqual(res["total"], 2)
        self.assertEqual(res["success_rate"], 0.5)
        self.assertEqual(res["avg_latency_ms"], 45.0)

    @patch("zapret_deck.autotune.test_connectivity")
    def test_rank_strategies(self, mock_test):
        mock_manager = MagicMock()

        strategies = [
            {"name": "StratBad", "args": "--filter-tcp=80,443 --dpi-desync=fake"},
            {"name": "StratGood", "args": "--filter-tcp=80,443 --dpi-desync=fake,split2"},
            {"name": "StratBest", "args": "--filter-tcp=80,443 --dpi-desync=multisplit"},
        ]

        def side_effect(targets, **kwargs):
            # Inspect what strategy zapret_manager was started with
            current_call_args = mock_manager.start.call_args[0][0]
            if "multisplit" in current_call_args:
                return {"success": True, "success_rate": 1.0, "avg_latency_ms": 40.0}
            elif "fake,split2" in current_call_args:
                return {"success": True, "success_rate": 1.0, "avg_latency_ms": 95.0}
            else:
                return {"success": False, "success_rate": 0.0, "avg_latency_ms": 0.0}

        mock_test.side_effect = side_effect

        auto_mgr = AutotuneManager(zapret_manager=mock_manager)
        ranked = auto_mgr.rank_strategies(strategies, delay_after_start=0.0)

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["name"], "StratBest")
        self.assertEqual(ranked[1]["name"], "StratGood")
        self.assertEqual(ranked[2]["name"], "StratBad")

    @patch("zapret_deck.autotune.test_connectivity")
    def test_tune_ttl(self, mock_test):
        mock_manager = MagicMock()
        base_args = "--filter-tcp=80,443 --dpi-desync=fake"

        def side_effect(targets, **kwargs):
            current_call_args = mock_manager.start.call_args[0][0]
            # TTL=4 works best
            if "--dpi-desync-ttl=4" in current_call_args:
                return {"success": True, "success_rate": 1.0, "avg_latency_ms": 35.0}
            elif "--dpi-desync-ttl=3" in current_call_args:
                return {"success": True, "success_rate": 0.5, "avg_latency_ms": 60.0}
            else:
                return {"success": False, "success_rate": 0.0, "avg_latency_ms": 0.0}

        mock_test.side_effect = side_effect

        auto_mgr = AutotuneManager(zapret_manager=mock_manager)
        res = auto_mgr.tune_ttl(base_args, ttl_range=range(1, 6), delay_after_start=0.0)

        self.assertTrue(res["success"])
        self.assertEqual(res["best_ttl"], 4)
        self.assertIn("--dpi-desync-ttl=4", res["best_strategy_args"])
        self.assertEqual(res["best_success_rate"], 1.0)
        self.assertEqual(res["best_latency_ms"], 35.0)


class TestAsyncAutotune(unittest.IsolatedAsyncioTestCase):
    @patch("zapret_deck.autotune.test_connectivity_async")
    async def test_rank_strategies_async(self, mock_test_async):
        mock_manager = MagicMock()
        strategies = [
            {"name": "Strat1", "args": "--dpi-desync=fake"},
            {"name": "Strat2", "args": "--dpi-desync=split2"},
        ]

        async def side_effect(targets, **kwargs):
            call_args = mock_manager.start.call_args[0][0]
            if "split2" in call_args:
                return {"success": True, "success_rate": 1.0, "avg_latency_ms": 30.0}
            return {"success": True, "success_rate": 0.5, "avg_latency_ms": 80.0}

        mock_test_async.side_effect = side_effect

        auto_mgr = AutotuneManager(zapret_manager=mock_manager)
        ranked = await auto_mgr.rank_strategies_async(strategies, delay_after_start=0.0)

        self.assertEqual(ranked[0]["name"], "Strat2")
        self.assertEqual(ranked[1]["name"], "Strat1")

    @patch("zapret_deck.autotune.test_connectivity_async")
    async def test_tune_ttl_async(self, mock_test_async):
        mock_manager = MagicMock()
        base_args = "--filter-tcp=80,443 --dpi-desync=fake"

        async def side_effect(targets, **kwargs):
            call_args = mock_manager.start.call_args[0][0]
            if "--dpi-desync-ttl=7" in call_args:
                return {"success": True, "success_rate": 1.0, "avg_latency_ms": 25.0}
            return {"success": False, "success_rate": 0.0, "avg_latency_ms": 0.0}

        mock_test_async.side_effect = side_effect

        auto_mgr = AutotuneManager(zapret_manager=mock_manager)
        res = await auto_mgr.tune_ttl_async(base_args, ttl_range=[5, 6, 7, 8], delay_after_start=0.0)

        self.assertTrue(res["success"])
        self.assertEqual(res["best_ttl"], 7)
        self.assertIn("--dpi-desync-ttl=7", res["best_strategy_args"])


if __name__ == "__main__":
    unittest.main()
