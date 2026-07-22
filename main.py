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
        
        # Гарантируем наличие файла списка хостов пользователя на старте
        if not os.path.exists(HOSTLIST_FILE):
            try:
                with open(HOSTLIST_FILE, "w") as f:
                    f.write("")
            except Exception as e:
                logger.error(f"Failed to create default empty hostlist: {e}")
        
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
        # Очистка сети при старте
        try:
            self.warp_manager.cleanup_network()
            self.zapret_manager.destroy_nftables()
        except Exception as e:
            decky.logger.error(f"Emergency cleanup on start failed: {e}")
            
        # Восстанавливаем сохраненное состояние служб
        if self.settings.get("zapret_enabled", False):
            strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
            decky.logger.info(f"Restoring Zapret Bypass on startup with strategy: {strategy}")
            self.zapret_manager.start(strategy, HOSTLIST_FILE)
            
        if self.settings.get("warp_enabled", False):
            decky.logger.info("Restoring WARP Bypass on startup")
            self.warp_manager.start()

    async def _unload(self):
        decky.logger.info("Zapret-Deck plugin unloading")
        self.zapret_manager.stop()
        self.warp_manager.stop()
        # Полностью удаляем правила nftables при выгрузке, сохраняя статус enabled в конфиге
        self.zapret_manager.destroy_nftables()

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
        current_args = self.settings.get("current_strategy", "")
        current_name = ""
        for s in DEFAULT_STRATEGIES:
            if s["args"] == current_args:
                current_name = s["name"]
                break
        return {
            "zapret_enabled": self.settings.get("zapret_enabled", False),
            "warp_enabled": self.settings.get("warp_enabled", False),
            "zapret_active": self.zapret_manager.is_running(),
            "warp_active": self.warp_manager.is_running(),
            "warp_registered": self.warp_manager.is_registered(),
            "autotune_in_progress": self.autotune_in_progress,
            "current_strategy": current_args,
            "current_strategy_name": current_name
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
        """Применяет выбранную стратегию. Если передана пустая строка, сбрасывает выбор и выключает службу."""
        self.settings["current_strategy"] = strategy_args
        if not strategy_args:
            self.settings["zapret_enabled"] = False
        self.save_settings()
        
        # Если сейчас включен zapret, перезапускаем его с новой стратегией (или выключаем при сбросе)
        if self.settings.get("zapret_enabled", False):
            if strategy_args:
                self.zapret_manager.start(strategy_args, HOSTLIST_FILE)
            else:
                self.zapret_manager.stop()
        else:
            self.zapret_manager.stop()
            
        return {"success": True, "strategy": strategy_args}

    @_rpc
    async def generate_warp(self) -> dict:
        """Регистрирует новый аккаунт WARP"""
        # Если zapret выключен, временно активируем его для связи с api.cloudflareclient.com в обход блокировок РКН
        zapret_was_active = self.zapret_manager.is_running()
        if not zapret_was_active:
            try:
                strategy = self.settings.get("current_strategy") or DEFAULT_STRATEGIES[0]["args"]
                self.zapret_manager.start(strategy, HOSTLIST_FILE)
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Failed to start temporary zapret for WARP reg: {e}")

        success = self.warp_manager.register()

        if not zapret_was_active:
            self.zapret_manager.stop()

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
        
        # Создаем временный список хостов для тестов автоподбора
        test_hostlist = os.path.join(SETTINGS_DIR, "autotune_hostlist.txt")
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            with open(test_hostlist, "w") as f:
                f.write("youtube.com\nwww.youtube.com\ngooglevideo.com\ngoogle.com\nwww.google.com\ndiscord.com\ngateway.discord.gg\n")
        except Exception as e:
            logger.error(f"Failed to create test hostlist: {e}")
            test_hostlist = HOSTLIST_FILE

        for i, strat in enumerate(DEFAULT_STRATEGIES):
            logger.info(f"Autotune testing: {strat['name']}")
            try:
                # Запускаем nfqws с этой стратегией и тестовым хостлистом
                self.zapret_manager.start(strat["args"], test_hostlist)
                await asyncio.sleep(3) # даем nfqws примениться
                
                # Тестируем доступность с обязательным флагом -4 (принудительно IPv4, исключая задержки IPv6)
                success = False
                for target_url in ["https://www.youtube.com", "https://www.google.com"]:
                    for attempt in range(2):
                        proc = await asyncio.create_subprocess_exec(
                            "/usr/bin/curl", "-4", "-s", "-I", "-k", "--connect-timeout", "4", target_url,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        
                        if proc.returncode == 0:
                            logger.info(f"Autotune target {target_url} HTTP check SUCCESS (rc=0)")
                            success = True
                            break
                        else:
                            err_msg = stderr.decode('utf-8', errors='ignore').strip()
                            logger.info(f"Autotune target {target_url} attempt {attempt+1} failed (rc={proc.returncode}): {err_msg}")
                        await asyncio.sleep(1)
                    if success:
                        break
                
                if success:
                     logger.info(f"Autotune success! Strategy works: {strat['name']}")
                     worked_strategy = strat["args"]
                     self.settings["autotuned_strategy_name"] = strat["name"]
                     self.save_settings()
                     break
            except Exception as e:
                logger.error(f"Error during autotune test {strat['name']}: {e}")

        # Удаляем временный файл хостлиста
        try:
            if os.path.exists(test_hostlist) and test_hostlist != HOSTLIST_FILE:
                os.remove(test_hostlist)
        except Exception as e:
            logger.error(f"Failed to remove test hostlist: {e}")

        self.autotune_in_progress = False
        self.zapret_manager.stop()

        if worked_strategy:
            self.settings["current_strategy"] = worked_strategy
            self.settings["zapret_enabled"] = True
            self.save_settings()
            # Запускаем окончательно с оригинальным списком хостов пользователя
            self.zapret_manager.start(worked_strategy, HOSTLIST_FILE)
            logger.info("Autotune complete. Applied working strategy and enabled Zapret Bypass.")
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
