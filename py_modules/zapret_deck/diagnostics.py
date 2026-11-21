"""
diagnostics.py - Network diagnostics, kernel module checks, and DoH DNS spoofing detection.
Compares local DNS resolution with trusted DoH providers (Cloudflare 1.1.1.1, Google 8.8.8.8).
Verifies kernel modules (nfnetlink_queue, nft_queue) and NFQUEUE state.
"""

import os
import json
import socket
import logging
import ipaddress
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("zapret-deck.diagnostics")

REQUIRED_MODULES = ["nfnetlink_queue", "nft_queue"]
DEFAULT_CHECK_DOMAINS = ["rutracker.org", "discord.com", "x.com"]

DOH_ENDPOINTS = {
    "cloudflare": "https://1.1.1.1/dns-query?name={domain}&type=A",
    "google": "https://8.8.8.8/resolve?name={domain}&type=A",
}

KNOWN_SINKHOLE_IPS = {
    "195.82.146.120", "195.82.146.121", "185.127.16.1", "82.193.100.200"
}


def is_bogon_or_sinkhole_ip(ip_str: str) -> bool:
    """Проверяет, является ли IP адрес локальным, приватным или известным заглушечным IP."""
    if ip_str in KNOWN_SINKHOLE_IPS:
        return True
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_loopback
            or ip.is_private
            or ip.is_reserved
            or ip.is_link_local
            or ip.is_unspecified
        )
    except ValueError:
        return False


def check_kernel_module(module_name: str) -> Dict[str, Any]:
    """Проверяет состояние модуля ядра через /proc/modules и /sys/module."""
    loaded = False
    builtin = False

    # 1. Проверяем /proc/modules
    proc_modules = "/proc/modules"
    if os.path.isfile(proc_modules):
        try:
            with open(proc_modules, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(f"{module_name} ") or line.startswith(f"{module_name}\t"):
                        loaded = True
                        break
        except Exception as e:
            logger.debug(f"Could not read /proc/modules: {e}")

    # 2. Проверяем /sys/module/<name>
    sys_dir = os.path.join("/sys/module", module_name)
    if os.path.isdir(sys_dir):
        if not loaded:
            builtin = True
        loaded = True

    return {
        "name": module_name,
        "loaded": loaded,
        "builtin": builtin,
        "available": loaded,
    }


def check_kernel_modules(modules: Optional[List[str]] = None) -> Dict[str, Any]:
    """Проверяет доступность всех требуемых модулей ядра netfilter."""
    target_modules = modules or REQUIRED_MODULES
    results = {}
    all_loaded = True
    for mod in target_modules:
        status = check_kernel_module(mod)
        results[mod] = status
        if not status["loaded"]:
            all_loaded = False
    return {
        "modules": results,
        "all_loaded": all_loaded,
    }


def ensure_kernel_module(module_name: str) -> Tuple[bool, str]:
    """Загружает модуль ядра через modprobe, если он не загружен."""
    status = check_kernel_module(module_name)
    if status["loaded"]:
        return True, "already loaded"
    try:
        res = subprocess.run(["modprobe", module_name], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return True, "loaded successfully"
        return False, res.stderr.strip() or "modprobe failed"
    except Exception as e:
        return False, str(e)


def check_nfqueue_status(queue_num: int = 220, proc_path: str = "/proc/net/netfilter/nfnetlink_queue") -> Dict[str, Any]:
    """Проверяет занятость очереди NFQUEUE по /proc/net/netfilter/nfnetlink_queue."""
    content = ""
    if os.path.isfile(proc_path):
        try:
            with open(proc_path, "r", encoding="utf-8") as f:
                content = f.read()
        except PermissionError:
            # Если нет прав на прямое чтение, пробуем прочитать через subproccess cat
            try:
                res = subprocess.run(["cat", proc_path], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    content = res.stdout
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Failed to read nfnetlink_queue: {e}")

    for line in content.splitlines():
        parts = line.split()
        if parts and parts[0] == str(queue_num):
            peer_port_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            queue_total = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            user_dropped = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0
            return {
                "queue_num": queue_num,
                "is_busy": True,
                "peer_port_id": peer_port_id,
                "queue_total": queue_total,
                "user_dropped": user_dropped,
            }

    return {
        "queue_num": queue_num,
        "is_busy": False,
        "peer_port_id": None,
        "queue_total": 0,
        "user_dropped": 0,
    }


def resolve_system_dns(domain: str, timeout: float = 3.0) -> List[str]:
    """Выполняет локальное разрешение DNS через системный сокет."""
    ips: List[str] = []
    try:
        orig_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            addr_info = socket.getaddrinfo(domain, 443, socket.AF_INET, socket.SOCK_STREAM)
            for item in addr_info:
                sockaddr = item[4]
                ip = sockaddr[0]
                if ip not in ips:
                    ips.append(ip)
        finally:
            socket.setdefaulttimeout(orig_timeout)
    except Exception as e:
        logger.debug(f"System DNS resolution failed for {domain}: {e}")
    return sorted(ips)


def resolve_doh(domain: str, provider: str = "cloudflare", timeout: float = 4.0) -> List[str]:
    """Разрешает домен через безопасный DoH (Cloudflare 1.1.1.1 или Google 8.8.8.8)."""
    endpoint_template = DOH_ENDPOINTS.get(provider, DOH_ENDPOINTS["cloudflare"])
    url = endpoint_template.format(domain=domain)
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/dns-json",
            "User-Agent": "zapret-deck-diagnostics/1.0",
        },
    )
    ips: List[str] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answers = data.get("Answer", [])
            for ans in answers:
                # Type 1 = A record (IPv4)
                if ans.get("type") == 1 and "data" in ans:
                    ip = ans["data"].strip()
                    if ip not in ips:
                        ips.append(ip)
    except Exception as e:
        logger.warning(f"DoH resolution ({provider}) failed for {domain}: {e}")
    return sorted(ips)


def check_dns_spoofing(domain: str, doh_provider: str = "cloudflare", timeout: float = 4.0) -> Dict[str, Any]:
    """
    Сравнивает системный DNS ответ с DoH ответом.
    Определяет подмену (DNS spoofing/poisoning/sinkholing).
    """
    system_ips = resolve_system_dns(domain, timeout=timeout)
    doh_ips = resolve_doh(domain, provider=doh_provider, timeout=timeout)

    is_spoofed = False
    reason = "DNS clean"

    # 1. Проверяем наличие bogon/заглушечных IP в системном ответе
    for sip in system_ips:
        if is_bogon_or_sinkhole_ip(sip):
            is_spoofed = True
            reason = f"System returned bogon/sinkhole IP: {sip}"
            break

    # 2. Если DoH вернул публичные IP, а системный DNS не вернул ничего или вернул чужой IP
    if not is_spoofed:
        if doh_ips and not system_ips:
            is_spoofed = True
            reason = "Domain blocked by local DNS (NXDOMAIN/Timeout)"
        elif doh_ips and system_ips:
            # Проверяем пересечение IP адресов
            common = set(system_ips).intersection(set(doh_ips))
            if not common:
                # Ни один IP не совпал - проверяем подсеть /24
                doh_subnets = {ip.rsplit(".", 1)[0] for ip in doh_ips}
                sys_subnets = {ip.rsplit(".", 1)[0] for ip in system_ips}
                if not doh_subnets.intersection(sys_subnets):
                    is_spoofed = True
                    reason = f"IP mismatch: System {system_ips} vs DoH {doh_ips}"

    status = "spoofed" if is_spoofed else ("error" if not system_ips and not doh_ips else "clean")

    return {
        "domain": domain,
        "is_spoofed": is_spoofed,
        "status": status,
        "reason": reason,
        "system_ips": system_ips,
        "doh_ips": doh_ips,
        "provider": doh_provider,
    }


def run_system_diagnostics(domains: Optional[List[str]] = None) -> Dict[str, Any]:
    """Комплексная сетевая диагностика: модули ядра, NFQUEUE и DNS-спуфинг."""
    modules_status = check_kernel_modules()
    queue_status = check_nfqueue_status(220)

    test_domains = domains or DEFAULT_CHECK_DOMAINS
    dns_results = [check_dns_spoofing(d) for d in test_domains]
    has_spoofing = any(r["is_spoofed"] for r in dns_results)

    overall_ok = modules_status["all_loaded"] and not queue_status["is_busy"] and not has_spoofing

    return {
        "overall_ok": overall_ok,
        "kernel_modules": modules_status,
        "nfqueue_220": queue_status,
        "dns_spoofing": {
            "has_spoofing": has_spoofing,
            "results": dns_results,
        },
    }
