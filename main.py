import os
import sys
import json
import logging
import asyncio
import subprocess
import functools
import traceback as _traceback

# Настройка путей для импорта
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

import decky

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zapret-deck")

from zapret_manager import ZapretManager
from warp_manager import WarpManager

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".config", "zapret-deck")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
HOSTLIST_FILE = os.path.join(SETTINGS_DIR, "hostlist.txt")

DEFAULT_STRATEGIES = [
    {
        "name": "YouTube/Discord (hostfakesplit)",
        "args": "--filter-tcp=443 --dpi-desync=hostfakesplit --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-hostfakesplit-mod=host=www.google.com"
    },
    {
        "name": "General Bypass (split2)",
        "args": "--filter-tcp=443 --dpi-desync=split2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig"
    },
    {
        "name": "Fake & TTL (fake/ttl)",
        "args": "--filter-tcp=443 --dpi-desync=fake --dpi-desync-autottl=2 --dpi-desync-repeats=6"
    },
    {
        "name": "Disorder (disorder)",
        "args": "--filter-tcp=443 --dpi-desync=disorder --dpi-desync-split-pos=1"
    }
]

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
        self.settings = {"mode": "off", "current_strategy": DEFAULT_STRATEGIES[0]["args"]}
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
            
        # Восстановление режима при запуске
        mode = self.settings.get("mode", "off")
        if mode == "zapret":
            try:
                strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
                self.zapret_manager.start(strategy)
            except Exception as e:
                decky.logger.error(f"Failed to restore zapret mode: {e}")
        elif mode == "warp":
            try:
                self.warp_manager.start()
            except Exception as e:
                decky.logger.error(f"Failed to restore warp mode: {e}")

    async def _unload(self):
        decky.logger.info("Zapret-Deck plugin unloading")
        self.zapret_manager.stop()
        self.warp_manager.stop()

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
            "mode": self.settings.get("mode", "off"),
            "zapret_active": self.zapret_manager.is_running(),
            "warp_active": self.warp_manager.is_running(),
            "warp_registered": self.warp_manager.is_registered(),
            "autotune_in_progress": self.autotune_in_progress,
            "current_strategy": self.settings.get("current_strategy", "")
        }

    @_rpc
    async def get_steam_language(self) -> str:
        """Возвращает язык интерфейса Steam"""
        try:
            return decky.arguments.get("language", "english")
        except Exception:
            return "english"

    @_rpc
    async def set_mode(self, mode: str) -> dict:
        """Переключает режим работы плагина"""
        if mode not in ["off", "zapret", "warp"]:
            return {"success": False, "error": f"Invalid mode: {mode}"}
            
        logger.info(f"Setting mode to: {mode}")
        self.settings["mode"] = mode
        self.save_settings()

        # Сначала всё тушим
        self.zapret_manager.stop()
        self.warp_manager.stop()

        if mode == "zapret":
            strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
            self.zapret_manager.start(strategy)
        elif mode == "warp":
            success = self.warp_manager.start()
            if not success:
                self.settings["mode"] = "off"
                self.save_settings()
                return {"success": False, "error": "Failed to start WARP connection"}

        return {"success": True, "mode": mode}

    @_rpc
    async def get_strategies(self) -> list:
        """Возвращает список доступных стратегий"""
        return DEFAULT_STRATEGIES

    @_rpc
    async def apply_strategy(self, strategy_args: str) -> dict:
        """Применяет выбранную стратегию"""
        self.settings["current_strategy"] = strategy_args
        self.save_settings()
        
        # Если сейчас включен zapret, перезапускаем его с новой стратегией
        if self.settings.get("mode") == "zapret":
            self.zapret_manager.start(strategy_args)
            
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
                self.zapret_manager.start(strat["args"])
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
                    break
            except Exception as e:
                logger.error(f"Error during autotune test {strat['name']}: {e}")

        self.autotune_in_progress = False
        self.zapret_manager.stop()

        if worked_strategy:
            self.settings["current_strategy"] = worked_strategy
            self.settings["mode"] = "zapret"
            self.save_settings()
            # Запускаем окончательно
            self.zapret_manager.start(worked_strategy)
            logger.info("Autotune complete. Applied working strategy.")
        else:
            logger.info("Autotune failed. No working strategy found.")
