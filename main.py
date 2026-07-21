import os
import sys
import json
import logging
import asyncio
import subprocess
import functools
import re
import traceback as _traceback

import decky

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zapret-deck")

from zapret_deck.zapret_manager import ZapretManager
from zapret_deck.warp_manager import WarpManager
from zapret_deck.strategies import DEFAULT_STRATEGIES

# Путь к директории плагина
plugin_dir = os.path.dirname(os.path.abspath(__file__))

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".config", "zapret-deck")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
HOSTLIST_FILE = os.path.join(SETTINGS_DIR, "hostlist.txt")

def _rpc(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)
        except Exception as e:
            tb = _traceback.format_exc()
            decky.logger.error(f"{func.__name__} exception: {tb}")
            return {"success": False, "error": f"{type(e).__name__}: {e}"}
    return wrapper

class Plugin:
    def __init__(self):
        self.settings = {"zapret_enabled": False, "warp_enabled": False, "current_strategy": DEFAULT_STRATEGIES[0]["args"]}
        self.autotune_in_progress = False
        
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        self.load_settings()
        
        self.zapret_manager = ZapretManager(plugin_dir)
        self.warp_manager = WarpManager(plugin_dir, SETTINGS_DIR)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        decky.logger.info("Zapret-Deck plugin initialized")
        # Аварийная очистка сети при старте
        try:
            self.warp_manager.cleanup_network()
            self.zapret_manager.clear_nftables()
        except Exception as e:
            decky.logger.error(f"Emergency cleanup on start failed: {e}")
            
        # Сетевая очистка при старте
        pass

    async def _unload(self):
        decky.logger.info("Zapret-Deck plugin unloading")
        self.zapret_manager.stop()
        self.warp_manager.stop()
        # Сбрасываем флаги активности при выходе, чтобы они не запускались сами
        self.settings["zapret_enabled"] = False
        self.settings["warp_enabled"] = False
        self.save_settings()

    async def _uninstall(self):
        decky.logger.info("Zapret-Deck plugin uninstalling")
        self.zapret_manager.stop()
        self.warp_manager.stop()
        try:
            if os.path.exists(SETTINGS_DIR):
                import shutil
                shutil.rmtree(SETTINGS_DIR)
        except Exception as e:
            decky.logger.error(f"Failed to delete settings dir during uninstall: {e}")

    # ── RPC API ────────────────────────────────────────────────────────

    @_rpc
    async def get_status(self) -> dict:
        """Возвращает статус плагина"""
        return {
            "zapret_enabled": self.settings.get("zapret_enabled", False),
            "warp_enabled": self.settings.get("warp_enabled", False),
            "zapret_active": self.zapret_manager.is_running(),
            "warp_active": self.warp_manager.is_running(),
            "warp_registered": self.warp_manager.is_registered(),
            "autotune_in_progress": self.autotune_in_progress,
            "current_strategy": self.settings.get("current_strategy", "")
        }

    @_rpc
    async def get_steam_language(self) -> str:
        """Считывает язык из Steam registry.vdf"""
        paths = []
        if os.path.isdir("/home"):
            try:
                for user in os.listdir("/home"):
                    if user != "lost+found":
                        paths.append(f"/home/{user}/.steam/registry.vdf")
                        paths.append(f"/home/{user}/.steam/steam/registry.vdf")
            except Exception:
                pass
        
        paths.append(os.path.expanduser("~/.steam/registry.vdf"))
        paths.append(os.path.expanduser("~/.steam/steam/registry.vdf"))
        
        for path in paths:
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    match = re.search(r'"language"\s+"([^"]+)"', content, re.IGNORECASE)
                    if match:
                        lang = match.group(1).lower().strip()
                        decky.logger.info(f"Steam language detected: {lang}")
                        return lang
                except Exception as e:
                    decky.logger.error(f"Error reading Steam language from {path}: {e}")
                    
        decky.logger.info("Steam language not found, defaulting to english")
        return "english"

    @_rpc
    async def set_service_state(self, service: str, enabled: bool) -> dict:
        """Включает или выключает указанный сервис (zapret или warp)"""
        if service not in ["zapret", "warp"]:
            return {"success": False, "error": f"Invalid service: {service}"}
            
        logger.info(f"Setting service {service} enabled to: {enabled}")
        self.settings[f"{service}_enabled"] = enabled
        self.save_settings()

        if service == "zapret":
            if enabled:
                strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
                self.zapret_manager.start(strategy, HOSTLIST_FILE)
            else:
                self.zapret_manager.stop()
        elif service == "warp":
            if enabled:
                success = self.warp_manager.start()
                if not success:
                    self.settings["warp_enabled"] = False
                    self.save_settings()
                    return {"success": False, "error": "Failed to start WARP connection"}
            else:
                self.warp_manager.stop()

        return {"success": True, "service": service, "enabled": enabled}

    @_rpc
    async def get_strategies(self) -> list:
        """Возвращает список доступных стратегий с отметкой автоподбора"""
        autotuned_name = self.settings.get("autotuned_strategy_name")
        if autotuned_name:
            updated_strats = []
            for s in DEFAULT_STRATEGIES:
                if s["name"] == autotuned_name:
                    updated_strats.append({
                        "name": f"{s['name']} (Auto)",
                        "args": s["args"]
                    })
                else:
                    updated_strats.append(s)
            return updated_strats
        return DEFAULT_STRATEGIES

    @_rpc
    async def apply_strategy(self, strategy_args: str) -> dict:
        """Применяет выбранную стратегию"""
        self.settings["current_strategy"] = strategy_args
        self.save_settings()
        
        # Если сейчас включен zapret, перезапускаем его с новой стратегией
        if self.settings.get("zapret_enabled", False):
            self.zapret_manager.start(strategy_args, HOSTLIST_FILE)
            
        return {"success": True, "strategy": strategy_args}

    @_rpc
    async def generate_warp(self) -> dict:
        """Регистрирует новый аккаунт WARP"""
        success = self.warp_manager.register()
        return {"success": success}

    @_rpc
    async def get_hostlist(self) -> str:
        """Читает список доменов"""
        if os.path.exists(HOSTLIST_FILE):
            try:
                with open(HOSTLIST_FILE, "r") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read hostlist: {e}")
        return ""

    @_rpc
    async def save_hostlist(self, hosts: str) -> dict:
        """Сохраняет список доменов"""
        try:
            with open(HOSTLIST_FILE, "w") as f:
                f.write(hosts)
            # Перезапускаем zapret, чтобы применить новый список хостов
            if self.settings.get("zapret_enabled", False):
                strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
                self.zapret_manager.start(strategy, HOSTLIST_FILE)
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to save hostlist: {e}")
            return {"success": False, "error": str(e)}

    @_rpc
    async def start_autotune(self) -> dict:
        """Запускает автоподбор стратегии в фоне"""
        if self.autotune_in_progress:
            return {"success": False, "error": "Autotune already in progress"}
            
        self.autotune_in_progress = True
        # Запускаем таску в asyncio loop, чтобы не блокировать RPC
        asyncio.create_task(self._run_autotune())
        return {"success": True}

    async def _run_autotune(self):
        logger.info("Starting background autotune...")
        self.zapret_manager.stop()
        self.warp_manager.stop()

        worked_strategy = None
        
        # Создаем минимальные правила nftables для тестов
        try:
            self.zapret_manager.setup_nftables()
        except Exception as e:
            logger.error(f"Failed to setup nftables for autotune: {e}")
            self.autotune_in_progress = False
            return

        for i, strat in enumerate(DEFAULT_STRATEGIES):
            logger.info(f"Autotune testing: {strat['name']}")
            try:
                # Запускаем nfqws с этой стратегией
                self.zapret_manager.start(strat["args"], HOSTLIST_FILE)
                await asyncio.sleep(3) # даем примениться
                
                # Тестируем доступность Google/YouTube
                proc = await asyncio.create_subprocess_exec(
                    "curl", "-s", "-I", "-k", "--connect-timeout", "4", "https://www.youtube.com",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                await proc.wait()
                
                if proc.returncode == 0:
                     logger.info(f"Autotune success! Strategy works: {strat['name']}")
                     worked_strategy = strat["args"]
                     self.settings["autotuned_strategy_name"] = strat["name"]
                     self.save_settings()
                     break
            except Exception as e:
                logger.error(f"Error during autotune test {strat['name']}: {e}")

        self.autotune_in_progress = False
        self.zapret_manager.stop()

        if worked_strategy:
            self.settings["current_strategy"] = worked_strategy
            self.settings["zapret_enabled"] = True
            self.save_settings()
            # Запускаем окончательно
            self.zapret_manager.start(worked_strategy, HOSTLIST_FILE)
            logger.info("Autotune complete. Applied working strategy.")
        else:
            logger.info("Autotune failed. No working strategy found.")

    @_rpc
    async def update_resources(self) -> dict:
        """Скачивает обновленные листы доменов с GitHub"""
        logger.info("Updating resources from GitHub...")
        
        lists_to_update = [
            "list-general.txt",
            "list-google.txt",
            "list-exclude.txt",
            "ipset-all.txt",
            "ipset-exclude.txt"
        ]
        
        lists_dir = os.path.join(plugin_dir, "lists")
        os.makedirs(lists_dir, exist_ok=True)
        
        updated_count = 0
        import urllib.request
        
        # Создаем SSL-контекст без проверки сертификатов для обхода проблем с CA-bundle на Steam Deck
        ssl_context = None
        try:
            import ssl
            ssl_context = ssl._create_unverified_context()
        except Exception:
            pass
            
        for lst in lists_to_update:
            url = f"https://raw.githubusercontent.com/Sergeydigl3/zapret-discord-youtube-linux/master/lists/{lst}"
            try:
                loop = asyncio.get_event_loop()
                def _download():
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                        return response.read()
                
                content = await loop.run_in_executor(None, _download)
                with open(os.path.join(lists_dir, lst), "wb") as f:
                    f.write(content)
                logger.info(f"Successfully updated list: {lst}")
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update list {lst}: {e}")
                
        # Если сейчас включен zapret, перезапускаем его
        if self.settings.get("zapret_enabled", False):
            strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
            self.zapret_manager.start(strategy, HOSTLIST_FILE)
            
        return {"success": True, "updated_lists": updated_count}
