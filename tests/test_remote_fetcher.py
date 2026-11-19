"""
tests/test_remote_fetcher.py - Unit tests for remote_fetcher.py (GitHub strategy fetcher).
"""

import os
import sys
import json
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

from zapret_deck.remote_fetcher import (
    get_repo_bat_files,
    fetch_bat_strategy,
    fetch_remote_strategies,
    save_strategies_to_json,
    RemoteFetcher,
    DEFAULT_BAT_FILES,
)


class TestRemoteFetcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.custom_file = os.path.join(self.temp_dir.name, "custom_strategies.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("urllib.request.urlopen")
    def test_get_repo_bat_files_from_api(self, mock_urlopen):
        """Проверка получения списка .bat файлов через GitHub API."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"name": "general.bat", "type": "file"},
            {"name": "discord.bat", "type": "file"},
            {"name": "README.md", "type": "file"},
        ]).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        files = get_repo_bat_files("Flowseal/zapret-discord-youtube")
        self.assertEqual(files, ["general.bat", "discord.bat"])

    @patch("urllib.request.urlopen", side_effect=Exception("API limit exceeded"))
    def test_get_repo_bat_files_fallback(self, mock_urlopen):
        """При сбое API возвращается список fallback по умолчанию."""
        files = get_repo_bat_files("Flowseal/zapret-discord-youtube")
        self.assertEqual(files, DEFAULT_BAT_FILES)

    @patch("zapret_deck.remote_fetcher.download_text")
    def test_fetch_bat_strategy(self, mock_download):
        """Успешное скачивание и парсинг .bat файла."""
        mock_download.return_value = (
            "@echo off\n"
            "start \"\" /min \"%BIN%winws.exe\" "
            "--wf-tcp=80,443 --filter-tcp=80,443 --dpi-desync=fake\n"
        )
        res = fetch_bat_strategy("Flowseal/zapret-discord-youtube", "main", "general (ALT).bat")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "general (ALT)")
        self.assertIn("--filter-tcp=80,443", res["args"])
        self.assertNotIn("--wf-tcp", res["args"])

    @patch("zapret_deck.remote_fetcher.download_text", return_value=None)
    def test_fetch_bat_strategy_failure(self, mock_download):
        """При ошибке загрузки возвращается None."""
        res = fetch_bat_strategy("Flowseal/zapret-discord-youtube", "main", "missing.bat")
        self.assertIsNone(res)

    @patch("zapret_deck.remote_fetcher.fetch_bat_strategy")
    def test_fetch_remote_strategies(self, mock_fetch_one):
        """Скачивание пачки файлов по списку."""
        mock_fetch_one.side_effect = [
            {"name": "strat1", "args": "--filter-tcp=80 --dpi-desync=fake"},
            None,
            {"name": "strat2", "args": "--filter-tcp=443 --dpi-desync=split2"},
        ]
        res = fetch_remote_strategies(files=["s1.bat", "bad.bat", "s2.bat"])
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "strat1")
        self.assertEqual(res[1]["name"], "strat2")

    def test_save_strategies_to_json(self):
        """Сохранение и слияние стратегий в JSON файл."""
        # 1. Первое сохранение
        strat1 = [{"name": "StratA", "args": "--args1"}]
        count = save_strategies_to_json(strat1, self.custom_file, merge=True)
        self.assertEqual(count, 1)

        # 2. Добавление новой стратегии и обновление существующей
        strat2 = [
            {"name": "StratA", "args": "--args1-updated"},
            {"name": "StratB", "args": "--args2"},
        ]
        count2 = save_strategies_to_json(strat2, self.custom_file, merge=True)
        self.assertEqual(count2, 2)

        with open(self.custom_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        saved_dict = {s["name"]: s["args"] for s in saved}
        self.assertEqual(saved_dict["StratA"], "--args1-updated")
        self.assertEqual(saved_dict["StratB"], "--args2")

    @patch("zapret_deck.remote_fetcher.fetch_remote_strategies")
    def test_remote_fetcher_sync(self, mock_fetch):
        """Интеграционный тест класса RemoteFetcher."""
        mock_fetch.return_value = [
            {"name": "Remote1", "args": "--dpi-desync=fake"},
            {"name": "Remote2", "args": "--dpi-desync=split2"},
        ]
        fetcher = RemoteFetcher(custom_file=self.custom_file)
        res = fetcher.sync()

        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 2)
        self.assertEqual(res["downloaded_count"], 2)
        self.assertTrue(os.path.isfile(self.custom_file))

    @patch("zapret_deck.remote_fetcher.fetch_remote_strategies", return_value=[])
    def test_remote_fetcher_sync_empty(self, mock_fetch):
        """Обработка пустого результата загрузки."""
        fetcher = RemoteFetcher(custom_file=self.custom_file)
        res = fetcher.sync()
        self.assertFalse(res["success"])
        self.assertEqual(res["count"], 0)


if __name__ == "__main__":
    unittest.main()
