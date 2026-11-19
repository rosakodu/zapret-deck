import os
import sys
import json
import logging
import asyncio
import subprocess
import functools
import inspect
import re
import traceback as _traceback

# Путь к директории плагина
plugin_dir = os.path.dirname(os.path.abspath(__file__))
py_modules_dir = os.path.join(plugin_dir, "py_modules")
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)
if py_modules_dir not in sys.path:
    sys.path.insert(0, py_modules_dir)

try:
    import decky
except ImportError:
    from unittest.mock import MagicMock
    decky = MagicMock()

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zapret-deck")

from zapret_deck.zapret_manager import ZapretManager
from zapret_deck.warp_manager import WarpManager
from zapret_deck.strategies import DEFAULT_STRATEGIES
from zapret_deck.server import ZapretDeckApiServer
from zapret_deck.bat_parser import parse_strategy_string, ParsedStrategy
from zapret_deck.fakes_manager import FakesManager
from zapret_deck.autotune import AutotuneManager, inject_ttl
from zapret_deck.diagnostics import run_system_diagnostics, check_nfqueue_status
from zapret_deck.gamefilter import GameFilterManager
from zapret_deck.remote_fetcher import RemoteFetcher
from tray.desktop_integration import (
    set_autostart,
    get_desktop_integration_status,
    launch_tray_process,
    kill_tray_process,
)

USER_HOME = "/home/deck" if os.path.isdir("/home/deck") else os.path.expanduser("~")
SETTINGS_DIR = os.path.join(USER_HOME, ".config", "zapret-deck")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
HOSTLIST_FILE = os.path.join(SETTINGS_DIR, "hostlist.txt")
CUSTOM_STRATEGIES_FILE = os.path.join(SETTINGS_DIR, "custom_strategies.json")

def _rpc(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            if inspect.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)
        except Exception as e:
            tb = _traceback.format_exc()
            decky.logger.error(f"{func.__name__} exception: {tb}")
            return {"success": False, "error": f"{type(e).__name__}: {e}"}
    return wrapper

class Plugin:
    def __init__(self):
        self.plugin_dir = plugin_dir
        self.api_server = None
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

        # Гарантируем наличие файла пользовательских стратегий на старте
        if not os.path.exists(CUSTOM_STRATEGIES_FILE):
            try:
                with open(CUSTOM_STRATEGIES_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Failed to create default custom_strategies.json: {e}")

        # Обеспечиваем права доступа пользователю deck в Desktop Mode
        if os.path.isdir("/home/deck"):
            try:
                import shutil
                shutil.chown(SETTINGS_DIR, user="deck", group="deck")
                if os.path.exists(HOSTLIST_FILE):
                    shutil.chown(HOSTLIST_FILE, user="deck", group="deck")
                if os.path.exists(CUSTOM_STRATEGIES_FILE):
                    shutil.chown(CUSTOM_STRATEGIES_FILE, user="deck", group="deck")
            except Exception:
                pass
        
        self.zapret_manager = ZapretManager(plugin_dir)
        self.warp_manager = WarpManager(plugin_dir, SETTINGS_DIR)
        self.autotune_manager = AutotuneManager(zapret_manager=self.zapret_manager)
        self.remote_fetcher = RemoteFetcher(custom_file=CUSTOM_STRATEGIES_FILE)

        # Восстанавливаем состояние GameFilter
        if "gamefilter_enabled" in self.settings:
            if self.settings["gamefilter_enabled"]:
                self.zapret_manager.game_filter.enable()
            else:
                self.zapret_manager.game_filter.disable()

    def get_all_strategies(self) -> list:
        """Возвращает список стандартных и пользовательских стратегий"""
        strategies = list(DEFAULT_STRATEGIES)
        if os.path.isfile(CUSTOM_STRATEGIES_FILE):
            try:
                with open(CUSTOM_STRATEGIES_FILE, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                    if isinstance(custom, list):
                        for item in custom:
                            if isinstance(item, dict) and "name" in item and "args" in item:
                                strategies.append({
                                    "name": f"{item['name']} [User]",
                                    "args": item["args"]
                                })
            except Exception as e:
                decky.logger.error(f"Failed to load custom strategies: {e}")
        return strategies

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

        # Запускаем локальный IPC API сервер для системного трея в режиме рабочего стола
        self.api_server = ZapretDeckApiServer(self, logger=decky.logger)
        await self.api_server.start()

        # Автозапуск системного трея на рабочем столе (включен по умолчанию)
        tray_enabled = self.settings.get("desktop_tray_enabled", True)
        if "desktop_tray_enabled" not in self.settings:
            self.settings["desktop_tray_enabled"] = True
            self.save_settings()

        if tray_enabled:
            loop = asyncio.get_running_loop()
            try:
                await loop.run_in_executor(None, set_autostart, self.plugin_dir, True)
                await loop.run_in_executor(None, launch_tray_process, self.plugin_dir)
            except Exception as e:
                decky.logger.error(f"Failed to start desktop tray: {e}")

    async def _unload(self):
        decky.logger.info("Zapret-Deck plugin unloading")
        if self.api_server:
            try:
                await self.api_server.stop()
            except Exception as e:
                decky.logger.error(f"Error stopping API server: {e}")
        self.zapret_manager.stop()
        self.warp_manager.stop()
        # Полностью удаляем правила nftables при выгрузке, сохраняя статус enabled в конфиге
        self.zapret_manager.destroy_nftables()

    async def _uninstall(self):
        decky.logger.info("Zapret-Deck plugin uninstalling")
        if self.api_server:
            try:
                await self.api_server.stop()
            except Exception:
                pass
        try:
            set_autostart(self.plugin_dir, False)
            kill_tray_process()
        except Exception:
            pass
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
        for s in self.get_all_strategies():
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
        all_strats = self.get_all_strategies()
        autotuned_name = self.settings.get("autotuned_strategy_name")
        if autotuned_name:
            updated_strats = []
            for s in all_strats:
                if s["name"] == autotuned_name:
                    updated_strats.append({
                        "name": f"{s['name']} (Auto)",
                        "args": s["args"]
                    })
                else:
                    updated_strats.append(s)
            return updated_strats
        return all_strats

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
        """Регистрирует новый аккаунт WARP с автоподбором подходящей стратегии обхода"""
        zapret_was_active = self.zapret_manager.is_running()
        active_strategy = self.settings.get("current_strategy")
        
        # Составляем список стратегий для попыток регистрации
        strats_to_try = []
        if active_strategy:
            strats_to_try.append(active_strategy)
        for s in self.get_all_strategies():
            if s["args"] not in strats_to_try:
                strats_to_try.append(s["args"])

        success = False
        for strat_args in strats_to_try:
            try:
                decky.logger.info("Attempting WARP registration with strategy...")
                self.zapret_manager.start(strat_args, HOSTLIST_FILE)
                await asyncio.sleep(2)
                if self.warp_manager.register():
                    success = True
                    decky.logger.info("WARP registration succeeded!")
                    break
            except Exception as e:
                decky.logger.error(f"Failed WARP reg attempt: {e}")

        # Восстанавливаем первоначальное состояние zapret
        if zapret_was_active and active_strategy:
            self.zapret_manager.start(active_strategy, HOSTLIST_FILE)
        elif not zapret_was_active:
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
        logger.info("Starting background autotune with TLS 1.3 socket testing...")
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

        try:
            strategies = self.get_all_strategies()
            ranked = await self.autotune_manager.rank_strategies_async(
                strategies,
                hostlist_file=test_hostlist,
                delay_after_start=2.5,
            )

            for strat_result in ranked:
                if strat_result["success"]:
                    logger.info(
                        f"Autotune success! Strategy works: {strat_result['name']} "
                        f"(success_rate={strat_result['success_rate']}, latency={strat_result['avg_latency_ms']}ms)"
                    )
                    worked_strategy = strat_result["args"]
                    self.settings["autotuned_strategy_name"] = strat_result["name"]
                    self.save_settings()
                    break
        except Exception as e:
            logger.error(f"Error during autotune test: {e}")

        # Удаляем временный файл хостлиста
        try:
            if os.path.exists(test_hostlist) and test_hostlist != HOSTLIST_FILE:
                os.remove(test_hostlist)
        except Exception as e:
            logger.error(f"Failed to remove test hostlist: {e}")

        self.zapret_manager.stop()

        if worked_strategy:
            self.settings["current_strategy"] = worked_strategy
            self.settings["zapret_enabled"] = True
            self.save_settings()
            # Запускаем окончательно с оригинальным списком хостов пользователя
            self.zapret_manager.start(worked_strategy, HOSTLIST_FILE)
            logger.info("Autotune complete. Applied working strategy and enabled Zapret Bypass.")
            await asyncio.sleep(1)
        else:
            self.settings["zapret_enabled"] = False
            self.save_settings()
            logger.info("Autotune failed. No working strategy found.")

        # В самом конце сбрасываем флаг подбора, когда служба уже полностью запущена
        self.autotune_in_progress = False

    @_rpc
    async def start_ttl_tune(self, strategy_args: str = None, ttl_min: int = 1, ttl_max: int = 20) -> dict:
        """Подбирает оптимальный TTL для стратегии через прямое сокетное тестирование"""
        target_strategy = strategy_args or self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
        logger.info(f"Starting TTL tuning (range {ttl_min}-{ttl_max}) for strategy...")

        ttl_range = range(max(1, ttl_min), min(255, ttl_max) + 1)
        res = await self.autotune_manager.tune_ttl_async(
            target_strategy,
            ttl_range=ttl_range,
            hostlist_file=HOSTLIST_FILE,
            delay_after_start=1.5,
        )

        if res["success"]:
            best_args = res["best_strategy_args"]
            self.settings["current_strategy"] = best_args
            self.save_settings()
            if self.settings.get("zapret_enabled", False):
                self.zapret_manager.start(best_args, HOSTLIST_FILE)
            logger.info(f"TTL tuning succeeded: best TTL={res['best_ttl']}")

        return {
            "success": res["success"],
            "best_ttl": res["best_ttl"],
            "best_strategy_args": res["best_strategy_args"],
            "best_success_rate": res["best_success_rate"],
            "best_latency_ms": res["best_latency_ms"],
        }

    @_rpc
    async def get_available_fakes(self) -> dict:
        """Возвращает список всех доступных .bin фейков и активный Discord UDP фейк"""
        fakes = self.zapret_manager.fakes_manager.list_available_fakes()
        active = self.zapret_manager.fakes_manager.get_active_fake()
        return {
            "success": True,
            "fakes": fakes,
            "active_fake": active,
        }

    @_rpc
    async def set_active_fake(self, fake_name: str) -> dict:
        """Устанавливает активный Discord UDP фейк и перезапускает zapret при необходимости"""
        success = self.zapret_manager.fakes_manager.set_active_fake(fake_name)
        if success and self.settings.get("zapret_enabled", False):
            strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
            self.zapret_manager.start(strategy, HOSTLIST_FILE)
        return {
            "success": success,
            "active_fake": fake_name,
        }

    @_rpc
    async def parse_bat_strategy(self, bat_content_or_path: str, name: str = "") -> dict:
        """Парсит Windows .bat файл или строку стратегии в Linux аргументы nfqws"""
        parsed = parse_strategy_string(bat_content_or_path, name=name)
        return {
            "success": True,
            "strategy": parsed.to_dict(),
        }

    @_rpc
    async def get_diagnostics(self) -> dict:
        """Запускает полную сетевую диагностику (модули ядра, NFQUEUE, DoH DNS-спуфинг)"""
        results = run_system_diagnostics()
        return {
            "success": True,
            "diagnostics": results,
        }

    @_rpc
    async def check_queue_status(self) -> dict:
        """Возвращает информацию о доступности и состоянии очереди NFQUEUE 220"""
        status = check_nfqueue_status(220)
        return {
            "success": True,
            "queue": status,
        }

    @_rpc
    async def get_gamefilter_config(self) -> dict:
        """Возвращает текущую конфигурацию защиты игрового UDP трафика (GameFilter)"""
        cfg = self.zapret_manager.game_filter.to_dict()
        return {
            "success": True,
            "config": cfg,
        }

    @_rpc
    async def set_gamefilter_enabled(self, enabled: bool) -> dict:
        """Включает или выключает GameFilter и динамически обновляет nftables"""
        if enabled:
            self.zapret_manager.game_filter.enable()
        else:
            self.zapret_manager.game_filter.disable()

        self.settings["gamefilter_enabled"] = bool(enabled)
        self.save_settings()

        if self.settings.get("zapret_enabled", False):
            strategy = self.settings.get("current_strategy", DEFAULT_STRATEGIES[0]["args"])
            parsed = self.zapret_manager.parse_strategy(strategy)
            self.zapret_manager.setup_nftables(parsed.tcp_ports, parsed.udp_ports)

        return {
            "success": True,
            "enabled": self.zapret_manager.game_filter.is_enabled(),
        }

    @_rpc
    async def sync_remote_strategies(self, repo: str = None, branch: str = None) -> dict:
        """Загружает свежие .bat стратегии из GitHub репозитория в custom_strategies.json"""
        res = self.remote_fetcher.sync(repo=repo, branch=branch, merge=True)
        return res

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

    @_rpc
    async def open_url(self, url: str) -> dict:
        """Открывает веб-страницу в браузере"""
        logger.info(f"Opening URL in browser: {url}")
        try:
            import subprocess
            clean_env = os.environ.copy()
            clean_env.pop("LD_LIBRARY_PATH", None)
            subprocess.Popen(["xdg-open", url], env=clean_env)
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return {"success": False, "error": str(e)}

    @_rpc
    async def get_desktop_tray_status(self) -> dict:
        """Возвращает статус интеграции с системным треем рабочего стола"""
        enabled = self.settings.get("desktop_tray_enabled", True)
        status = get_desktop_integration_status(self.plugin_dir)
        return {"enabled": enabled, "autostart": status.get("autostart", False)}

    @_rpc
    async def set_desktop_tray_enabled(self, enable: bool) -> dict:
        """Переключает статус интеграции с системным треем и автозапуск"""
        self.settings["desktop_tray_enabled"] = enable
        self.save_settings()
        loop = asyncio.get_running_loop()
        if enable:
            await loop.run_in_executor(None, set_autostart, self.plugin_dir, True)
            await loop.run_in_executor(None, launch_tray_process, self.plugin_dir)
        else:
            await loop.run_in_executor(None, set_autostart, self.plugin_dir, False)
            await loop.run_in_executor(None, kill_tray_process)
        return {"success": True, "enabled": enable}


