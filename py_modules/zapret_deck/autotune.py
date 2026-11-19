"""
autotune.py - Direct socket TLS 1.3 testing, strategy ranking, and TTL tuning.
Performs native socket TLS handshakes (without external curl), ranks strategies,
and tunes packet TTL (1-20) via --dpi-desync-ttl injection for zapret-deck.
"""

import os
import re
import ssl
import time
import socket
import shlex
import asyncio
import logging
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    from zapret_deck.bat_parser import normalize_path_token
except ImportError:
    from .bat_parser import normalize_path_token

logger = logging.getLogger("zapret-deck.autotune")

DEFAULT_TARGET_HOSTS = [
    "www.youtube.com",
    "www.google.com",
    "discord.com",
]

DEFAULT_TIMEOUT_SEC = 3.5
DEFAULT_PORT = 443
MIN_TTL = 1
MAX_TTL = 20


@dataclass
class TLSCheckResult:
    host: str
    port: int
    success: bool
    latency_ms: float
    error: Optional[str] = None
    tls_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "success": self.success,
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
            "tls_version": self.tls_version,
        }


def clean_host(target: str) -> str:
    """Извлекает имя хоста из URL или строки хост:порт."""
    trimmed = target.strip()
    if "://" in trimmed:
        parsed = urlparse(trimmed)
        return parsed.hostname or trimmed
    if ":" in trimmed:
        return trimmed.split(":", 1)[0]
    return trimmed


def check_tls_handshake(
    host: str,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    enforce_tls13: bool = True,
) -> TLSCheckResult:
    """
    Выполняет прямой сокетный TLS 1.3 ClientHello handshake к целевому хосту (IPv4).
    Измеряет время установки соединения без сторонних curl процессов.
    """
    clean_hostname = clean_host(host)
    start_time = time.perf_counter()

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    if enforce_tls13:
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
            ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        except Exception as e:
            logger.debug(f"Could not enforce TLS 1.3 version: {e}")

    try:
        # Принудительно используем IPv4 (AF_INET), аналогично curl -4
        addr_infos = socket.getaddrinfo(clean_hostname, port, socket.AF_INET, socket.SOCK_STREAM)
        if not addr_infos:
            latency = (time.perf_counter() - start_time) * 1000.0
            return TLSCheckResult(
                host=clean_hostname,
                port=port,
                success=False,
                latency_ms=latency,
                error="No IPv4 address resolved",
            )

        sock_addr = addr_infos[0][4]

        # Установка TCP соединения с таймаутом
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(timeout)
        raw_sock.connect(sock_addr)

        # Выполнение TLS ClientHello handshake
        with ctx.wrap_socket(raw_sock, server_hostname=clean_hostname) as ssock:
            tls_ver = ssock.version()
            latency = (time.perf_counter() - start_time) * 1000.0
            return TLSCheckResult(
                host=clean_hostname,
                port=port,
                success=True,
                latency_ms=latency,
                tls_version=tls_ver,
            )

    except Exception as exc:
        latency = (time.perf_counter() - start_time) * 1000.0
        return TLSCheckResult(
            host=clean_hostname,
            port=port,
            success=False,
            latency_ms=latency,
            error=str(exc),
        )


async def check_tls_handshake_async(
    host: str,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    enforce_tls13: bool = True,
) -> TLSCheckResult:
    """Асинхронная обертка для check_tls_handshake."""
    return await asyncio.to_thread(
        check_tls_handshake, host, port, timeout, enforce_tls13
    )


def test_connectivity(
    targets: Optional[List[str]] = None,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    retries: int = 1,
    enforce_tls13: bool = True,
) -> Dict[str, Any]:
    """
    Проверяет доступность списка хостов через TLS handshake.
    Возвращает статистику успешности и среднюю задержку.
    """
    if not targets:
        targets = list(DEFAULT_TARGET_HOSTS)

    results: List[TLSCheckResult] = []
    success_count = 0
    total_latency = 0.0

    for target in targets:
        target_success = False
        best_res = None

        for _ in range(retries):
            res = check_tls_handshake(target, port=port, timeout=timeout, enforce_tls13=enforce_tls13)
            if res.success:
                target_success = True
                best_res = res
                break
            best_res = res

        if best_res:
            results.append(best_res)
            if target_success:
                success_count += 1
                total_latency += best_res.latency_ms

    total = len(targets)
    avg_latency = (total_latency / success_count) if success_count > 0 else 0.0
    success_rate = (success_count / total) if total > 0 else 0.0

    return {
        "success": success_count > 0,
        "success_rate": round(success_rate, 2),
        "success_count": success_count,
        "total": total,
        "avg_latency_ms": round(avg_latency, 2),
        "results": [r.to_dict() for r in results],
    }


async def test_connectivity_async(
    targets: Optional[List[str]] = None,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    retries: int = 1,
    enforce_tls13: bool = True,
) -> Dict[str, Any]:
    """Асинхронная проверка доступности хостов."""
    return await asyncio.to_thread(
        test_connectivity, targets, port, timeout, retries, enforce_tls13
    )


def inject_ttl(strategy_args: str, ttl: int) -> str:
    """
    Внедряет или заменяет параметр --dpi-desync-ttl=<ttl> в аргументах стратегии.
    Инжектирует параметр во все блоки desync (разделенные --new).
    """
    if ttl < 1:
        ttl = 1
    elif ttl > 255:
        ttl = 255

    try:
        tokens = shlex.split(strategy_args)
    except Exception:
        tokens = strategy_args.split()

    new_tokens: List[str] = []
    has_desync_in_block = False
    has_ttl_in_block = False

    for tok in tokens:
        if tok == "--new":
            if has_desync_in_block and not has_ttl_in_block:
                new_tokens.append(f"--dpi-desync-ttl={ttl}")
            new_tokens.append(tok)
            has_desync_in_block = False
            has_ttl_in_block = False
            continue

        if tok.startswith("--dpi-desync-ttl="):
            new_tokens.append(f"--dpi-desync-ttl={ttl}")
            has_ttl_in_block = True
        elif tok.startswith("--dpi-desync="):
            new_tokens.append(tok)
            has_desync_in_block = True
        else:
            norm = normalize_path_token(tok)
            new_tokens.append(norm)

    if has_desync_in_block and not has_ttl_in_block:
        new_tokens.append(f"--dpi-desync-ttl={ttl}")

    return " ".join(new_tokens)


class AutotuneManager:
    """Управление тестированием, ранжированием стратегий и подбором TTL."""

    def __init__(
        self,
        zapret_manager=None,
        default_targets: Optional[List[str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SEC,
    ):
        self.zapret_manager = zapret_manager
        self.default_targets = default_targets or list(DEFAULT_TARGET_HOSTS)
        self.timeout = timeout

    def rank_strategies(
        self,
        strategies: List[Dict[str, Any]],
        targets: Optional[List[str]] = None,
        hostlist_file: Optional[str] = None,
        delay_after_start: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """
        Тестирует и ранжирует список стратегий по успешности и latency.
        Возвращает отсортированный список стратегий.
        """
        targets = targets or self.default_targets
        ranked: List[Dict[str, Any]] = []

        for strat in strategies:
            strat_name = strat.get("name", "Unknown")
            strat_args = strat.get("args", "")
            logger.info(f"Autotune testing strategy: {strat_name}")

            if self.zapret_manager:
                try:
                    self.zapret_manager.start(strat_args, hostlist_file=hostlist_file)
                    time.sleep(delay_after_start)
                except Exception as e:
                    logger.error(f"Failed to start zapret with strategy {strat_name}: {e}")
                    ranked.append({
                        "name": strat_name,
                        "args": strat_args,
                        "success": False,
                        "success_rate": 0.0,
                        "avg_latency_ms": 9999.0,
                        "error": str(e),
                    })
                    continue

            metrics = test_connectivity(targets, timeout=self.timeout)
            ranked.append({
                "name": strat_name,
                "args": strat_args,
                "success": metrics["success"],
                "success_rate": metrics["success_rate"],
                "avg_latency_ms": metrics["avg_latency_ms"],
                "metrics": metrics,
            })

        # Ранжирование: сначала наибольший success_rate, затем наименьший avg_latency_ms
        ranked.sort(key=lambda s: (-s["success_rate"], s["avg_latency_ms"]))
        return ranked

    async def rank_strategies_async(
        self,
        strategies: List[Dict[str, Any]],
        targets: Optional[List[str]] = None,
        hostlist_file: Optional[str] = None,
        delay_after_start: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Асинхронная версия ранжирования стратегий."""
        targets = targets or self.default_targets
        ranked: List[Dict[str, Any]] = []

        for strat in strategies:
            strat_name = strat.get("name", "Unknown")
            strat_args = strat.get("args", "")
            logger.info(f"Async autotune testing strategy: {strat_name}")

            if self.zapret_manager:
                try:
                    self.zapret_manager.start(strat_args, hostlist_file=hostlist_file)
                    await asyncio.sleep(delay_after_start)
                except Exception as e:
                    logger.error(f"Failed to start zapret with strategy {strat_name}: {e}")
                    ranked.append({
                        "name": strat_name,
                        "args": strat_args,
                        "success": False,
                        "success_rate": 0.0,
                        "avg_latency_ms": 9999.0,
                        "error": str(e),
                    })
                    continue

            metrics = await test_connectivity_async(targets, timeout=self.timeout)
            ranked.append({
                "name": strat_name,
                "args": strat_args,
                "success": metrics["success"],
                "success_rate": metrics["success_rate"],
                "avg_latency_ms": metrics["avg_latency_ms"],
                "metrics": metrics,
            })

        ranked.sort(key=lambda s: (-s["success_rate"], s["avg_latency_ms"]))
        return ranked

    def tune_ttl(
        self,
        base_strategy_args: str,
        ttl_range: Optional[Union[range, List[int]]] = None,
        targets: Optional[List[str]] = None,
        hostlist_file: Optional[str] = None,
        delay_after_start: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Перебирает TTL от MIN_TTL до MAX_TTL и подбирает оптимальное значение.
        """
        if ttl_range is None:
            ttl_range = range(MIN_TTL, MAX_TTL + 1)
        targets = targets or self.default_targets

        results_by_ttl: Dict[int, Dict[str, Any]] = {}
        best_ttl = None
        best_success_rate = 0.0
        best_latency = float("inf")

        for ttl in ttl_range:
            injected_args = inject_ttl(base_strategy_args, ttl)
            logger.info(f"Testing TTL={ttl}...")

            if self.zapret_manager:
                try:
                    self.zapret_manager.start(injected_args, hostlist_file=hostlist_file)
                    time.sleep(delay_after_start)
                except Exception as e:
                    logger.error(f"Failed to start zapret with TTL={ttl}: {e}")
                    results_by_ttl[ttl] = {"success": False, "error": str(e)}
                    continue

            metrics = test_connectivity(targets, timeout=self.timeout)
            results_by_ttl[ttl] = metrics

            s_rate = metrics["success_rate"]
            lat = metrics["avg_latency_ms"]

            if s_rate > best_success_rate or (s_rate == best_success_rate and s_rate > 0 and lat < best_latency):
                best_success_rate = s_rate
                best_latency = lat
                best_ttl = ttl

        best_args = inject_ttl(base_strategy_args, best_ttl) if best_ttl else base_strategy_args
        return {
            "success": best_ttl is not None and best_success_rate > 0,
            "best_ttl": best_ttl,
            "best_strategy_args": best_args,
            "best_success_rate": best_success_rate,
            "best_latency_ms": round(best_latency, 2) if best_latency != float("inf") else 0.0,
            "results_by_ttl": results_by_ttl,
        }

    async def tune_ttl_async(
        self,
        base_strategy_args: str,
        ttl_range: Optional[Union[range, List[int]]] = None,
        targets: Optional[List[str]] = None,
        hostlist_file: Optional[str] = None,
        delay_after_start: float = 1.5,
    ) -> Dict[str, Any]:
        """Асинхронный подбор TTL."""
        if ttl_range is None:
            ttl_range = range(MIN_TTL, MAX_TTL + 1)
        targets = targets or self.default_targets

        results_by_ttl: Dict[int, Dict[str, Any]] = {}
        best_ttl = None
        best_success_rate = 0.0
        best_latency = float("inf")

        for ttl in ttl_range:
            injected_args = inject_ttl(base_strategy_args, ttl)
            logger.info(f"Async testing TTL={ttl}...")

            if self.zapret_manager:
                try:
                    self.zapret_manager.start(injected_args, hostlist_file=hostlist_file)
                    await asyncio.sleep(delay_after_start)
                except Exception as e:
                    logger.error(f"Failed to start zapret with TTL={ttl}: {e}")
                    results_by_ttl[ttl] = {"success": False, "error": str(e)}
                    continue

            metrics = await test_connectivity_async(targets, timeout=self.timeout)
            results_by_ttl[ttl] = metrics

            s_rate = metrics["success_rate"]
            lat = metrics["avg_latency_ms"]

            if s_rate > best_success_rate or (s_rate == best_success_rate and s_rate > 0 and lat < best_latency):
                best_success_rate = s_rate
                best_latency = lat
                best_ttl = ttl

        best_args = inject_ttl(base_strategy_args, best_ttl) if best_ttl else base_strategy_args
        return {
            "success": best_ttl is not None and best_success_rate > 0,
            "best_ttl": best_ttl,
            "best_strategy_args": best_args,
            "best_success_rate": best_success_rate,
            "best_latency_ms": round(best_latency, 2) if best_latency != float("inf") else 0.0,
            "results_by_ttl": results_by_ttl,
        }
