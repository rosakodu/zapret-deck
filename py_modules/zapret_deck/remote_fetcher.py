"""
remote_fetcher.py - Download and parse Windows .bat strategies from GitHub upstream.
Converts remote .bat files to Linux nfqws format and saves them to custom_strategies.json.
"""

import os
import ssl
import json
import logging
import tempfile
import urllib.parse
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

try:
    from zapret_deck.bat_parser import parse_bat_content
except ImportError:
    from .bat_parser import parse_bat_content

logger = logging.getLogger("zapret-deck.fetcher")

DEFAULT_UPSTREAM_REPO = "Flowseal/zapret-discord-youtube"
DEFAULT_BRANCH = "main"

# Common default strategy files from Flowseal repo
DEFAULT_BAT_FILES = [
    "general.bat",
    "general (ALT).bat",
    "general (ALT 2).bat",
    "general (ALT 3).bat",
    "general (ALT 4).bat",
    "general (ALT 5).bat",
    "general (ALT 6).bat",
    "general (ALT 7).bat",
    "general (ALT 8).bat",
    "general (ALT 9).bat",
    "general (ALT 10).bat",
    "general (ALT 11).bat",
    "general (ALT 12).bat",
    "general (FAKE TLS AUTO ALT).bat",
    "general (FAKE TLS AUTO ALT2).bat",
    "general (FAKE TLS AUTO ALT3).bat",
    "discord.bat",
]


def _get_ssl_context() -> ssl.SSLContext:
    """Создает SSL контекст без строгой верификации для совместимости со SteamOS."""
    try:
        return ssl._create_unverified_context()
    except Exception:
        return ssl.create_default_context()


def download_text(url: str, timeout: int = 10) -> Optional[str]:
    """Загружает текстовое содержимое по HTTP/HTTPS URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "zapret-deck/1.0"})
    try:
        ctx = _get_ssl_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw_bytes = resp.read()
            # Windows .bat файлы часто в cp1251 или utf-8
            try:
                return raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return raw_bytes.decode("cp1251", errors="replace")
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return None


def get_repo_bat_files(repo: str = DEFAULT_UPSTREAM_REPO, branch: str = DEFAULT_BRANCH, timeout: int = 10) -> List[str]:
    """Получает список .bat файлов из репозитория через GitHub API или fallback."""
    api_url = f"https://api.github.com/repos/{repo}/contents?ref={branch}"
    req = urllib.request.Request(api_url, headers={
        "User-Agent": "zapret-deck/1.0",
        "Accept": "application/vnd.github.v3+json",
    })
    try:
        ctx = _get_ssl_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                files = [
                    item["name"]
                    for item in data
                    if isinstance(item, dict) and item.get("name", "").lower().endswith(".bat")
                ]
                if files:
                    return files
    except Exception as e:
        logger.debug(f"GitHub API listing failed for {repo}: {e}, using default fallback list")

    return list(DEFAULT_BAT_FILES)


def fetch_bat_strategy(repo: str, branch: str, filename: str, timeout: int = 10) -> Optional[Dict[str, str]]:
    """Скачивает и парсит один .bat файл стратегии."""
    quoted = urllib.parse.quote(filename)
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{quoted}"
    content = download_text(raw_url, timeout=timeout)
    if not content:
        return None

    clean_name = filename
    if clean_name.lower().endswith(".bat"):
        clean_name = clean_name[:-4]
    elif clean_name.lower().endswith(".cmd"):
        clean_name = clean_name[:-4]

    parsed = parse_bat_content(content, name=clean_name)
    if parsed and parsed.clean_args:
        return {
            "name": clean_name,
            "args": parsed.clean_args,
        }
    return None


def fetch_remote_strategies(
    repo: str = DEFAULT_UPSTREAM_REPO,
    branch: str = DEFAULT_BRANCH,
    files: Optional[List[str]] = None,
    timeout: int = 10,
) -> List[Dict[str, str]]:
    """Скачивает и конвертирует список .bat стратегий из репозитория."""
    bat_list = files or get_repo_bat_files(repo, branch, timeout=timeout)
    strategies: List[Dict[str, str]] = []

    for fname in bat_list:
        strat = fetch_bat_strategy(repo, branch, fname, timeout=timeout)
        if strat:
            strategies.append(strat)

    return strategies


def save_strategies_to_json(
    strategies: List[Dict[str, str]],
    target_path: str,
    merge: bool = True,
) -> int:
    """Сохраняет стратегии в файл custom_strategies.json (с поддержкой слияния)."""
    existing_list: List[Dict[str, str]] = []
    if merge and os.path.isfile(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_list = data
        except Exception as e:
            logger.warning(f"Could not load existing strategies: {e}")

    # Индексируем по имени
    strat_map: Dict[str, str] = {s["name"]: s["args"] for s in existing_list if "name" in s and "args" in s}
    for s in strategies:
        strat_map[s["name"]] = s["args"]

    merged = [{"name": k, "args": v} for k, v in strat_map.items()]

    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    temp_fd, temp_file = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(target_path)), suffix=".json")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, target_path)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

    return len(merged)


class RemoteFetcher:
    """Менеджер синхронизации внешних стратегий zapret."""

    def __init__(
        self,
        custom_file: str,
        repo: str = DEFAULT_UPSTREAM_REPO,
        branch: str = DEFAULT_BRANCH,
    ):
        self.custom_file = custom_file
        self.repo = repo
        self.branch = branch

    def sync(
        self,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        files: Optional[List[str]] = None,
        merge: bool = True,
    ) -> Dict[str, Any]:
        """Загружает свежие стратегии и сохраняет их в custom_strategies.json."""
        target_repo = repo or self.repo
        target_branch = branch or self.branch

        try:
            downloaded = fetch_remote_strategies(target_repo, target_branch, files=files)
            if not downloaded:
                return {
                    "success": False,
                    "count": 0,
                    "strategies": [],
                    "error": "No valid strategies downloaded",
                }

            total_saved = save_strategies_to_json(downloaded, self.custom_file, merge=merge)
            return {
                "success": True,
                "count": total_saved,
                "downloaded_count": len(downloaded),
                "strategies": downloaded,
            }
        except Exception as e:
            logger.error(f"Failed to sync remote strategies: {e}")
            return {
                "success": False,
                "count": 0,
                "strategies": [],
                "error": str(e),
            }
