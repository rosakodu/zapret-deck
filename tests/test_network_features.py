"""
tests/test_network_features.py - Unit tests for:
1. GameFilter (py_modules/zapret_deck/gamefilter.py)
2. Network Diagnostics & DoH DNS Spoofing (py_modules/zapret_deck/diagnostics.py)
3. NFQUEUE 220 check and auto-cleanup in ZapretManager (py_modules/zapret_deck/zapret_manager.py)
"""

import os
import io
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Ensure root dir and py_modules are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_MODULES = os.path.join(BASE_DIR, "py_modules")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PY_MODULES not in sys.path:
    sys.path.insert(0, PY_MODULES)

from zapret_deck.gamefilter import (
    parse_port_entry,
    parse_ports_string,
    is_port_in_ranges,
    exclude_ports_from_string,
    GameFilterManager,
    DEFAULT_GAME_PRESETS,
)
from zapret_deck.diagnostics import (
    is_bogon_or_sinkhole_ip,
    check_kernel_module,
    check_kernel_modules,
    ensure_kernel_module,
    check_nfqueue_status,
    resolve_doh,
    check_dns_spoofing,
    run_system_diagnostics,
)
from zapret_deck.zapret_manager import ZapretManager, QUEUE_NUM, TABLE_NAME, CHAIN_NAME


class TestGameFilter(unittest.TestCase):
    """Тестирование модуля GameFilter."""

    def test_default_presets_presence(self):
        """Проверка наличия базовых пресетов игр."""
        expected_presets = ["steam", "source_cs2", "riot", "blizzard", "ea_apex", "epic_fortnite", "genshin", "console_p2p"]
        for preset in expected_presets:
            self.assertIn(preset, DEFAULT_GAME_PRESETS)
            self.assertTrue(len(DEFAULT_GAME_PRESETS[preset]) > 0)

    def test_parse_port_entry(self):
        """Проверка парсинга диапазонов и одиночных портов."""
        self.assertEqual(parse_port_entry("443"), (443, 443))
        self.assertEqual(parse_port_entry("27000-27100"), (27000, 27100))
        self.assertIsNone(parse_port_entry("invalid"))
        self.assertIsNone(parse_port_entry("70000"))
        self.assertIsNone(parse_port_entry("500-100"))  # start > end
        self.assertIsNone(parse_port_entry(""))

    def test_parse_ports_string(self):
        """Проверка парсинга составной строки портов."""
        res = parse_ports_string("80, 443, 27015-27030")
        self.assertEqual(res, [(80, 80), (443, 443), (27015, 27030)])

    def test_is_port_in_ranges(self):
        """Проверка попадания порта в диапазоны."""
        ranges = [(80, 80), (27000, 27100)]
        self.assertTrue(is_port_in_ranges(80, ranges))
        self.assertTrue(is_port_in_ranges(27015, ranges))
        self.assertFalse(is_port_in_ranges(443, ranges))
        self.assertFalse(is_port_in_ranges(27101, ranges))

    def test_exclude_ports_from_string(self):
        """Исключение защищенных диапазонов из строки портов."""
        ranges = [(27000, 27100)]
        result = exclude_ports_from_string("443, 27015, 50000", ranges)
        self.assertEqual(result, "443,50000")

    def test_game_filter_manager_filtering(self):
        """Проверка фильтрации портов через GameFilterManager."""
        gf = GameFilterManager(enabled=True)
        # Steam / Source порт 27015 должен определяться как игровой
        self.assertTrue(gf.is_game_port(27015))
        # Обычный порт 443 не игровой
        self.assertFalse(gf.is_game_port(443))

        filtered = gf.filter_udp_ports("443,27015,50000")
        self.assertEqual(filtered, "443,50000")

    def test_custom_ports(self):
        """Добавление и удаление пользовательских портов."""
        gf = GameFilterManager(enabled=True)
        self.assertTrue(gf.add_custom_port("12345"))
        self.assertTrue(gf.is_game_port(12345))
        self.assertIn("12345", gf.get_protected_port_specs())

        self.assertTrue(gf.remove_custom_port("12345"))
        self.assertFalse(gf.is_game_port(12345))

    def test_enable_disable(self):
        """Отключение GameFilter снимает фильтрацию."""
        gf = GameFilterManager(enabled=True)
        self.assertTrue(gf.is_game_port(27015))
        gf.disable()
        self.assertFalse(gf.is_enabled())
        self.assertFalse(gf.is_game_port(27015))
        self.assertEqual(gf.filter_udp_ports("443,27015"), "443,27015")

    def test_nftables_format(self):
        """Проверка генерации строки портов для nftables."""
        gf = GameFilterManager(enabled=True)
        nft_str = gf.get_nftables_ports()
        self.assertTrue(nft_str.startswith("{ "))
        self.assertTrue(nft_str.endswith(" }"))
        self.assertIn("27000-27100", nft_str)

    def test_serialization(self):
        """Проверка сохранения и восстановления состояния."""
        gf = GameFilterManager(enabled=True)
        gf.add_custom_port("11223")
        gf.set_preset_state("riot", False)
        data = gf.to_dict()

        gf2 = GameFilterManager()
        gf2.load_dict(data)
        self.assertTrue(gf2.is_enabled())
        self.assertIn("11223", gf2.custom_ports)
        self.assertFalse(gf2.preset_states["riot"])


class TestDiagnostics(unittest.TestCase):
    """Тестирование сетевой диагностики, DoH и проверки ядра."""

    def test_is_bogon_or_sinkhole_ip(self):
        """Проверка выявления заглушечных и приватных IP."""
        self.assertTrue(is_bogon_or_sinkhole_ip("127.0.0.1"))
        self.assertTrue(is_bogon_or_sinkhole_ip("0.0.0.0"))
        self.assertTrue(is_bogon_or_sinkhole_ip("192.168.1.100"))
        self.assertTrue(is_bogon_or_sinkhole_ip("10.0.0.1"))
        self.assertTrue(is_bogon_or_sinkhole_ip("195.82.146.120"))  # sinkhole
        self.assertFalse(is_bogon_or_sinkhole_ip("1.1.1.1"))
        self.assertFalse(is_bogon_or_sinkhole_ip("8.8.8.8"))
        self.assertFalse(is_bogon_or_sinkhole_ip("142.250.180.206"))

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    @patch("builtins.open", new_callable=mock_open, read_data="nfnetlink_queue 36864 1 - Live 0xffffffff\n")
    def test_check_kernel_module_loaded(self, mock_file, mock_isdir, mock_isfile):
        """Проверка обнаружения загруженного модуля ядра."""
        mock_isfile.return_value = True
        mock_isdir.return_value = True
        res = check_kernel_module("nfnetlink_queue")
        self.assertTrue(res["loaded"])
        self.assertEqual(res["name"], "nfnetlink_queue")

    @patch("os.path.isfile", return_value=False)
    @patch("os.path.isdir", return_value=False)
    def test_check_kernel_module_missing(self, mock_isdir, mock_isfile):
        """Проверка отсутствующего модуля ядра."""
        res = check_kernel_module("unknown_module")
        self.assertFalse(res["loaded"])
        self.assertFalse(res["available"])

    @patch("zapret_deck.diagnostics.check_kernel_module")
    @patch("subprocess.run")
    def test_ensure_kernel_module(self, mock_subproc, mock_check):
        """Проверка автозагрузки модуля через modprobe."""
        mock_check.return_value = {"loaded": False}
        mock_subproc.return_value = MagicMock(returncode=0, stderr="")
        ok, msg = ensure_kernel_module("nft_queue")
        self.assertTrue(ok)
        mock_subproc.assert_called_once_with(["modprobe", "nft_queue"], capture_output=True, text=True, timeout=5)

    @patch("os.path.isfile", return_value=True)
    def test_check_nfqueue_status_busy(self, mock_isfile):
        """Проверка определения занятости NFQUEUE 220."""
        proc_data = "  220  54321      10 2 65531     0     0    20249  1\n"
        with patch("builtins.open", mock_open(read_data=proc_data)):
            status = check_nfqueue_status(220)
            self.assertTrue(status["is_busy"])
            self.assertEqual(status["peer_pid"], 54321)
            self.assertEqual(status["queue_total"], 10)

    @patch("os.path.isfile", return_value=True)
    def test_check_nfqueue_status_free(self, mock_isfile):
        """Проверка свободной очереди NFQUEUE 220."""
        proc_data = "  100   1713      0 2 65531     0     0    20249  1\n"
        with patch("builtins.open", mock_open(read_data=proc_data)):
            status = check_nfqueue_status(220)
            self.assertFalse(status["is_busy"])
            self.assertIsNone(status["peer_pid"])

    @patch("urllib.request.urlopen")
    def test_resolve_doh(self, mock_urlopen):
        """Проверка DoH запроса через Cloudflare API."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "Answer": [
                {"name": "discord.com", "type": 1, "data": "162.159.138.232"},
                {"name": "discord.com", "type": 1, "data": "162.159.137.232"},
            ]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        ips = resolve_doh("discord.com", provider="cloudflare")
        self.assertIn("162.159.138.232", ips)
        self.assertIn("162.159.137.232", ips)

    @patch("zapret_deck.diagnostics.resolve_system_dns", return_value=["162.159.138.232"])
    @patch("zapret_deck.diagnostics.resolve_doh", return_value=["162.159.138.232"])
    def test_check_dns_spoofing_clean(self, mock_doh, mock_sys):
        """Проверка чистого DNS без подмены."""
        res = check_dns_spoofing("discord.com")
        self.assertFalse(res["is_spoofed"])
        self.assertEqual(res["status"], "clean")

    @patch("zapret_deck.diagnostics.resolve_system_dns", return_value=["127.0.0.1"])
    @patch("zapret_deck.diagnostics.resolve_doh", return_value=["104.21.5.10"])
    def test_check_dns_spoofing_loopback(self, mock_doh, mock_sys):
        """Обнаружение подмены DNS на петлевой адрес 127.0.0.1."""
        res = check_dns_spoofing("blocked.domain")
        self.assertTrue(res["is_spoofed"])
        self.assertEqual(res["status"], "spoofed")
        self.assertIn("bogon/sinkhole", res["reason"])

    @patch("zapret_deck.diagnostics.resolve_system_dns", return_value=[])
    @patch("zapret_deck.diagnostics.resolve_doh", return_value=["104.21.5.10"])
    def test_check_dns_spoofing_blocked(self, mock_doh, mock_sys):
        """Обнаружение блокировки через NXDOMAIN при успешном DoH."""
        res = check_dns_spoofing("blocked.domain")
        self.assertTrue(res["is_spoofed"])
        self.assertIn("blocked by local DNS", res["reason"])

    @patch("zapret_deck.diagnostics.check_kernel_modules")
    @patch("zapret_deck.diagnostics.check_nfqueue_status")
    @patch("zapret_deck.diagnostics.check_dns_spoofing")
    def test_run_system_diagnostics(self, mock_dns, mock_queue, mock_kernel):
        """Проверка запуска сводного отчета диагностики."""
        mock_kernel.return_value = {"all_loaded": True}
        mock_queue.return_value = {"is_busy": False}
        mock_dns.return_value = {"is_spoofed": False, "status": "clean"}

        diag = run_system_diagnostics(domains=["example.com"])
        self.assertTrue(diag["overall_ok"])
        self.assertFalse(diag["dns_spoofing"]["has_spoofing"])


class TestZapretManagerNetworkFeatures(unittest.TestCase):
    """Тестирование интеграции NFQUEUE 220 и GameFilter в ZapretManager."""

    def setUp(self):
        self.manager = ZapretManager(plugin_dir="/tmp/dummy_plugin")

    @patch("zapret_deck.zapret_manager.check_nfqueue_status")
    def test_is_nfqueue_busy(self, mock_queue_status):
        """Проверка вызова проверки занятости очереди."""
        mock_queue_status.return_value = {"is_busy": True, "peer_pid": 9999}
        self.assertTrue(self.manager.is_nfqueue_busy(220))

        mock_queue_status.return_value = {"is_busy": False, "peer_pid": None}
        self.assertFalse(self.manager.is_nfqueue_busy(220))

    @patch.object(ZapretManager, "is_nfqueue_busy", return_value=False)
    @patch.object(ZapretManager, "clear_nftables")
    @patch.object(ZapretManager, "_run_cmd", return_value=(0, "", ""))
    @patch("zapret_deck.zapret_manager.check_nfqueue_status", return_value={"peer_pid": 12345})
    def test_cleanup_nfqueue(self, mock_status, mock_run_cmd, mock_clear, mock_busy):
        """Проверка завершения процесса, удерживающего очередь, и очистки nftables."""
        success = self.manager.cleanup_nfqueue(220)
        self.assertTrue(success)
        mock_clear.assert_called_once()
        # Проверяем отправку сигналов завершения процессу PID 12345
        kill_cmds = [call[0][0] for call in mock_run_cmd.call_args_list]
        self.assertIn(["kill", "-15", "12345"], kill_cmds)
        self.assertIn(["kill", "-9", "12345"], kill_cmds)

    @patch.object(ZapretManager, "is_nfqueue_busy", return_value=True)
    @patch.object(ZapretManager, "cleanup_nfqueue", return_value=True)
    def test_ensure_queue_available_triggers_cleanup(self, mock_cleanup, mock_busy):
        """Если очередь занята, вызывается автоочистка."""
        res = self.manager.ensure_queue_available(220)
        self.assertTrue(res)
        mock_cleanup.assert_called_once_with(220)

    @patch.object(ZapretManager, "clear_nftables")
    @patch.object(ZapretManager, "_run_cmd", return_value=(0, "", ""))
    def test_setup_nftables_with_gamefilter_bypass(self, mock_run_cmd, mock_clear):
        """Проверка добавления правила accept bypass для игровых портов перед NFQUEUE."""
        self.manager.game_filter.enable()
        self.manager.setup_nftables(tcp_ports="80,443", udp_ports="443", enable_game_filter=True)

        calls = [c[0][0] for c in mock_run_cmd.call_args_list]
        bypass_calls = [
            cmd for cmd in calls
            if "zapret-deck-gamefilter-bypass" in " ".join(cmd)
        ]
        self.assertEqual(len(bypass_calls), 1)
        bypass_rule = bypass_calls[0]
        self.assertIn("accept", bypass_rule)
        self.assertIn("udp", bypass_rule)

    @patch.object(ZapretManager, "clear_nftables")
    @patch.object(ZapretManager, "_run_cmd", return_value=(0, "", ""))
    def test_setup_nftables_without_gamefilter(self, mock_run_cmd, mock_clear):
        """Если GameFilter выключен, правило bypass не добавляется."""
        self.manager.setup_nftables(tcp_ports="80,443", udp_ports="443", enable_game_filter=False)
        calls = [c[0][0] for c in mock_run_cmd.call_args_list]
        bypass_calls = [cmd for cmd in calls if "zapret-deck-gamefilter-bypass" in " ".join(cmd)]
        self.assertEqual(len(bypass_calls), 0)


if __name__ == "__main__":
    unittest.main()
