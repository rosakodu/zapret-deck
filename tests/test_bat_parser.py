"""
Tests for bat_parser, fakes_manager, and ZapretManager integration.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure root dir and py_modules are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_MODULES = os.path.join(BASE_DIR, "py_modules")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PY_MODULES not in sys.path:
    sys.path.insert(0, PY_MODULES)

from zapret_deck.bat_parser import (
    parse_strategy_string,
    parse_bat_content,
    parse_bat_file,
    extract_ports,
    clean_tokens,
    normalize_path_token,
    DEFAULT_TCP_PORTS,
    DEFAULT_UDP_PORTS,
)
from zapret_deck.fakes_manager import (
    FakesManager,
    ACTIVE_DISCORD_FAKE_NAME,
    DEFAULT_DISCORD_FAKE_SOURCE,
    GAME_FILTER_UDP_PORTS,
    GAME_FILTER_TCP_PORTS,
)
from zapret_deck.zapret_manager import ZapretManager


class TestBatParser(unittest.TestCase):
    def test_parse_simple_strategy(self):
        cmd = "--filter-tcp=80,443 --dpi-desync=split2"
        res = parse_strategy_string(cmd)
        self.assertEqual(res.tcp_ports, "80,443")
        self.assertEqual(res.udp_ports, DEFAULT_UDP_PORTS)
        self.assertIn("--filter-tcp=80,443", res.clean_args)
        self.assertIn("--dpi-desync=split2", res.clean_args)
        self.assertEqual(res.clean_args_list, ["--filter-tcp=80,443", "--dpi-desync=split2"])

    def test_extract_wf_ports(self):
        cmd = (
            "--wf-tcp=80,443,2053,8443 --wf-udp=443,19294-19344,50000-50100 "
            "--filter-tcp=80,443 --dpi-desync=fake"
        )
        res = parse_strategy_string(cmd)
        self.assertEqual(res.tcp_ports, "80,443,2053,8443")
        self.assertEqual(res.udp_ports, "443,19294-19344,50000-50100")
        self.assertNotIn("--wf-tcp", res.clean_args)
        self.assertNotIn("--wf-udp", res.clean_args)
        self.assertNotIn("--wf-tcp", " ".join(res.clean_args_list))
        self.assertNotIn("--wf-udp", " ".join(res.clean_args_list))

    def test_port_fallback_from_filter(self):
        cmd = (
            "--filter-tcp=80,443 --dpi-desync=fake --new "
            "--filter-tcp=8443,2053 --dpi-desync=split2 --new "
            "--filter-udp=443,50000-50100 --dpi-desync=fake"
        )
        res = parse_strategy_string(cmd)
        self.assertEqual(res.tcp_ports, "80,443,8443,2053")
        self.assertEqual(res.udp_ports, "443,50000-50100")

    def test_default_ports_fallback(self):
        cmd = "--dpi-desync=fake --dpi-desync-fooling=ts"
        res = parse_strategy_string(cmd)
        self.assertEqual(res.tcp_ports, DEFAULT_TCP_PORTS)
        self.assertEqual(res.udp_ports, DEFAULT_UDP_PORTS)

    def test_bat_file_line_continuation_and_comments(self):
        bat_content = """@echo off
chcp 65001 >nul
:: Discord and Youtube bypass
REM Flowseal style config
set BIN=%~dp0bin\\
set LISTS=%~dp0lists\\
call service.bat load_game_filter

start "zapret" /min "%BIN%winws.exe" ^
--wf-tcp=80,443,2053,8443 --wf-udp=443,50000-50100 ^
--filter-udp=443 --hostlist="%LISTS%\\list-general.txt" --dpi-desync=fake --dpi-desync-fake-quic="%BIN%\\quic_initial.bin" --new ^
--filter-tcp=80,443 --hostlist="%~dp0lists\\list-general.txt" --dpi-desync=fake,split2
"""
        res = parse_bat_content(bat_content, name="flowseal_test")
        self.assertEqual(res.name, "flowseal_test")
        self.assertEqual(res.tcp_ports, "80,443,2053,8443")
        self.assertEqual(res.udp_ports, "443,50000-50100")
        self.assertNotIn("start", res.clean_args)
        self.assertNotIn("winws", res.clean_args)
        self.assertNotIn("/min", res.clean_args)
        self.assertNotIn("--wf-tcp", res.clean_args)
        self.assertIn('--hostlist="%LISTS%list-general.txt"', res.clean_args)
        self.assertIn('--dpi-desync-fake-quic="%BIN%quic_initial.bin"', res.clean_args)

    def test_clean_empty_filters(self):
        cmd = (
            "--filter-tcp=80,443 --dpi-desync=fake --new "
            "--filter-tcp= --filter-udp= --filter-l7= --dpi-desync=fake"
        )
        res = parse_strategy_string(cmd)
        self.assertNotIn("--filter-tcp=", [t for t in res.clean_args_list if t == "--filter-tcp="])
        self.assertNotIn("--filter-udp=", [t for t in res.clean_args_list if t == "--filter-udp="])
        self.assertNotIn("--filter-l7=", [t for t in res.clean_args_list if t == "--filter-l7="])

    def test_path_normalization(self):
        tokens = [
            '--dpi-desync-fake-quic="%BIN%\\quic_initial.bin"',
            '--hostlist="%~dp0lists\\list-general.txt"',
            '--dpi-desync-fake-discord=bin/ACTIVE_DISCORD_UDP.bin',
            '--filter-tcp=80,443',
        ]
        norm = [normalize_path_token(t) for t in tokens]
        self.assertEqual(norm[0], '--dpi-desync-fake-quic="%BIN%quic_initial.bin"')
        self.assertEqual(norm[1], '--hostlist="%LISTS%list-general.txt"')
        self.assertEqual(norm[2], '--dpi-desync-fake-discord="%BIN%ACTIVE_DISCORD_UDP.bin"')
        self.assertEqual(norm[3], '--filter-tcp=80,443')

    def test_parse_bat_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".bat", delete=False) as f:
            f.write("""@echo off
start "%BIN%winws.exe" --wf-tcp=80,443 --filter-tcp=80,443 --dpi-desync=fake
""")
            temp_path = f.name

        try:
            res = parse_bat_file(temp_path)
            self.assertEqual(res.tcp_ports, "80,443")
            self.assertEqual(res.udp_ports, DEFAULT_UDP_PORTS)
            self.assertIn("--filter-tcp=80,443", res.clean_args)
        finally:
            os.remove(temp_path)


class TestFakesManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bin_dir = os.path.join(self.temp_dir.name, "bin")
        self.shared_dir = os.path.join(self.temp_dir.name, "shared")
        os.makedirs(self.bin_dir, exist_ok=True)
        os.makedirs(os.path.join(self.shared_dir, "bin"), exist_ok=True)

        # Create sample fakes
        self.fake1_path = os.path.join(self.bin_dir, DEFAULT_DISCORD_FAKE_SOURCE)
        with open(self.fake1_path, "wb") as f:
            f.write(b"DBANK_FAKE_DATA_12345")

        self.fake2_path = os.path.join(self.bin_dir, "stun.bin")
        with open(self.fake2_path, "wb") as f:
            f.write(b"STUN_DATA_67890")

        self.fakes_mgr = FakesManager(bin_dir=self.bin_dir, shared_dir=self.shared_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ensure_active_fake(self):
        active_path = self.fakes_mgr.ensure_active_fake()
        self.assertTrue(os.path.isfile(active_path))
        self.assertEqual(os.path.basename(active_path), ACTIVE_DISCORD_FAKE_NAME)

        # Check content matches DEFAULT_DISCORD_FAKE_SOURCE
        with open(active_path, "rb") as f:
            content = f.read()
        self.assertEqual(content, b"DBANK_FAKE_DATA_12345")

        # Verify synced to shared dir
        shared_active = os.path.join(self.shared_dir, "bin", ACTIVE_DISCORD_FAKE_NAME)
        self.assertTrue(os.path.isfile(shared_active))

    def test_set_active_fake_and_list(self):
        self.fakes_mgr.ensure_active_fake()
        fakes = self.fakes_mgr.list_available_fakes()
        self.assertEqual(len(fakes), 2)

        # Default source should be marked active
        dbank_fake = next(f for f in fakes if f["name"] == DEFAULT_DISCORD_FAKE_SOURCE)
        self.assertTrue(dbank_fake["is_active"])

        # Switch active fake to stun.bin
        success = self.fakes_mgr.set_active_fake("stun.bin")
        self.assertTrue(success)

        # Re-list and verify active changed
        fakes_after = self.fakes_mgr.list_available_fakes()
        stun_fake = next(f for f in fakes_after if f["name"] == "stun.bin")
        self.assertTrue(stun_fake["is_active"])

        dbank_after = next(f for f in fakes_after if f["name"] == DEFAULT_DISCORD_FAKE_SOURCE)
        self.assertFalse(dbank_after["is_active"])

    def test_game_filter_ports(self):
        ports = self.fakes_mgr.get_game_filter_ports()
        self.assertEqual(ports["tcp"], GAME_FILTER_TCP_PORTS)
        self.assertEqual(ports["udp"], GAME_FILTER_UDP_PORTS)


class TestZapretManagerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plugin_dir = self.temp_dir.name
        self.bin_dir = os.path.join(self.plugin_dir, "bin")
        self.lists_dir = os.path.join(self.plugin_dir, "lists")
        os.makedirs(self.bin_dir, exist_ok=True)
        os.makedirs(self.lists_dir, exist_ok=True)

        # Fake nfqws binary and sample fakes
        with open(os.path.join(self.bin_dir, "nfqws"), "w") as f:
            f.write("#!/bin/sh\nexit 0\n")
        with open(os.path.join(self.bin_dir, DEFAULT_DISCORD_FAKE_SOURCE), "wb") as f:
            f.write(b"SAMPLE_FAKE")

        self.manager = ZapretManager(self.plugin_dir, shared_dir=os.path.join(self.plugin_dir, "shared"))

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("subprocess.Popen")
    @patch.object(ZapretManager, "_owns_queue", return_value=True)
    @patch.object(ZapretManager, "is_nfqueue_busy", return_value=False)
    @patch.object(ZapretManager, "setup_nftables")
    @patch.object(ZapretManager, "clear_nftables")
    @patch.object(ZapretManager, "_run_cmd", return_value=(0, "", ""))
    def test_start_with_bat_parsing(
        self, mock_run_cmd, mock_clear_nft, mock_setup_nft, mock_busy, mock_owns_queue, mock_popen
    ):
        mock_popen.return_value.poll.return_value = None
        strategy = (
            '--wf-tcp=80,443,2053 --wf-udp=443,50000-50100 '
            '--filter-tcp=80,443 --hostlist="%LISTS%list.txt" '
            '--dpi-desync-fake-quic="%BIN%quic.bin"'
        )
        self.manager.start(strategy)

        # setup_nftables must be called with parsed ports
        mock_setup_nft.assert_called_once_with("80,443,2053", "443,50000-50100")

        # Popen must be called with resolved shared paths and without --wf-* flags
        self.assertTrue(mock_popen.called)
        called_args = mock_popen.call_args[0][0]
        self.assertNotIn("--daemon", called_args)
        self.assertNotIn("--wf-tcp=80,443,2053", called_args)
        self.assertNotIn("--wf-udp=443,50000-50100", called_args)
        expected_shared_lists = os.path.join(self.plugin_dir, "shared", "lists", "list.txt")
        expected_shared_bin = os.path.join(self.plugin_dir, "shared", "bin", "quic.bin")
        self.assertIn(f"--hostlist={expected_shared_lists}", called_args)
        self.assertIn(f"--dpi-desync-fake-quic={expected_shared_bin}", called_args)

    @patch("subprocess.Popen")
    @patch.object(ZapretManager, "is_nfqueue_busy", return_value=False)
    @patch.object(ZapretManager, "setup_nftables")
    @patch.object(ZapretManager, "clear_nftables")
    @patch.object(ZapretManager, "_run_cmd", return_value=(0, "", ""))
    def test_early_exit_cleans_up_without_installing_rules(
        self, mock_run_cmd, mock_clear_nft, mock_setup_nft, mock_busy, mock_popen
    ):
        mock_popen.return_value.poll.return_value = 2
        with self.assertRaisesRegex(RuntimeError, "nfqws exited with code 2"):
            self.manager.start("--filter-tcp=443")
        mock_setup_nft.assert_not_called()
        mock_clear_nft.assert_called_once()
        self.assertFalse(self.manager.is_running())

    def test_parse_strategy_method(self):
        parsed = self.manager.parse_strategy("--wf-tcp=80,443 --filter-tcp=80,443 --dpi-desync=split2")
        self.assertEqual(parsed.tcp_ports, "80,443")
        self.assertIn("--dpi-desync=split2", parsed.clean_args)


if __name__ == "__main__":
    unittest.main()
