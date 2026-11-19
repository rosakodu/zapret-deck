"""
bat_parser.py - Parser for Windows .bat/.cmd scripts and winws/nfqws arguments.
Converts Windows winws strategies and batch files into Linux nfqws arguments,
extracts TCP and UDP ports, adapts path variables, and cleans incompatible flags.
"""

import os
import re
import shlex
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional

DEFAULT_TCP_PORTS = "80,443"
DEFAULT_UDP_PORTS = "443"

# Windows and daemon flags to strip from Linux nfqws arguments
STRIP_FLAG_PREFIXES = (
    "--wf-tcp=",
    "--wf-udp=",
    "--wf-raw=",
    "--wf-l3=",
    "--wf-filter=",
    "--windivert=",
    "--daemon",
    "--pidfile",
    "--user=",
    "--qnum=",
)

# Empty filters that crash nfqws v72.5
EMPTY_FILTER_FLAGS = (
    "--filter-tcp=",
    "--filter-udp=",
    "--filter-l7=",
)

# Executables and launcher keywords to strip
LAUNCHER_TOKENS = {
    "winws",
    "winws.exe",
    "nfqws",
    "start",
    "call",
    "/min",
    "/b",
    "/high",
    "/realtime",
    "/abovenormal",
    "/belownormal",
    "/low",
    "/wait",
}


@dataclass
class ParsedStrategy:
    name: str
    tcp_ports: str
    udp_ports: str
    clean_args: str
    clean_args_list: List[str] = field(default_factory=list)
    raw_cmd: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tcp_ports": self.tcp_ports,
            "udp_ports": self.udp_ports,
            "clean_args": self.clean_args,
            "clean_args_list": list(self.clean_args_list),
            "raw_cmd": self.raw_cmd,
        }


def _deduplicate_ports(port_strings: List[str]) -> str:
    """Нормализует и дедуплицирует список портов и диапазонов с сохранением порядка."""
    seen = set()
    result = []
    for item in port_strings:
        if not item:
            continue
        for p in item.split(","):
            p = p.strip()
            if p and p not in seen:
                seen.add(p)
                result.append(p)
    return ",".join(result)


def extract_ports(tokens: List[str]) -> Tuple[str, str]:
    """
    Извлекает порты TCP и UDP из аргументов.
    Приоритет:
    1. Явные флаги --wf-tcp и --wf-udp.
    2. Флаги --filter-tcp и --filter-udp.
    3. Значения по умолчанию (80,443 для TCP, 443 для UDP).
    """
    wf_tcp_list = []
    wf_udp_list = []
    filter_tcp_list = []
    filter_udp_list = []

    for token in tokens:
        if token.startswith("--wf-tcp="):
            val = token.split("=", 1)[1].strip()
            if val:
                wf_tcp_list.append(val)
        elif token.startswith("--wf-udp="):
            val = token.split("=", 1)[1].strip()
            if val:
                wf_udp_list.append(val)
        elif token.startswith("--filter-tcp="):
            val = token.split("=", 1)[1].strip()
            if val:
                filter_tcp_list.append(val)
        elif token.startswith("--filter-udp="):
            val = token.split("=", 1)[1].strip()
            if val:
                filter_udp_list.append(val)

    # TCP ports resolution
    if wf_tcp_list:
        tcp_ports = _deduplicate_ports(wf_tcp_list)
    elif filter_tcp_list:
        tcp_ports = _deduplicate_ports(filter_tcp_list)
    else:
        tcp_ports = DEFAULT_TCP_PORTS

    # UDP ports resolution
    if wf_udp_list:
        udp_ports = _deduplicate_ports(wf_udp_list)
    elif filter_udp_list:
        udp_ports = _deduplicate_ports(filter_udp_list)
    else:
        udp_ports = DEFAULT_UDP_PORTS

    return tcp_ports, udp_ports


def normalize_path_token(token: str) -> str:
    """
    Адаптирует пути к файлам в аргументах для Linux.
    Преобразует Windows пути и переменные (%~dp0, %BIN%, %LISTS%) в стандартные плейсхолдеры.
    """
    if not token.startswith("--") or "=" not in token:
        return token

    key, val = token.split("=", 1)
    val = val.strip("\"'")

    # Преобразуем обратные слэши в прямые
    val = val.replace("\\\\", "/").replace("\\", "/")

    # Заменяем вариации путей к bin и lists на стандартные плейсхолдеры
    val = re.sub(r"(%~dp0)?bin/", "%BIN%", val, flags=re.IGNORECASE)
    val = re.sub(r"%BIN%/", "%BIN%", val, flags=re.IGNORECASE)
    val = re.sub(r"(%~dp0)?lists/", "%LISTS%", val, flags=re.IGNORECASE)
    val = re.sub(r"%LISTS%/", "%LISTS%", val, flags=re.IGNORECASE)

    # Если в пути фигурирует %BIN% или %LISTS%, оборачиваем значение в кавычки
    if "%BIN%" in val or "%LISTS%" in val or " " in val:
        return f'{key}="{val}"'
    return f"{key}={val}"


def clean_tokens(tokens: List[str]) -> List[str]:
    """
    Удаляет Windows-специфичные флаги, пустые фильтры и некорректные токены.
    """
    cleaned: List[str] = []

    for token in tokens:
        stripped = token.strip()
        if not stripped:
            continue

        # Пропускаем пустые фильтры (ломают nfqws)
        if stripped in EMPTY_FILTER_FLAGS:
            continue
        if any(stripped.startswith(prefix) for prefix in ("--filter-tcp=", "--filter-udp=")) and not stripped.split("=", 1)[1].strip():
            continue

        # Пропускаем winws флаги и параметры демона
        if any(stripped.startswith(prefix) for prefix in STRIP_FLAG_PREFIXES):
            continue
        if stripped in ("--daemon", "--pidfile"):
            continue

        # Пропускаем токены запуска исполнимых файлов
        norm_name = os.path.basename(stripped.strip("\"'")).lower()
        if norm_name in LAUNCHER_TOKENS:
            continue

        # Адаптируем пути в токене
        token_norm = normalize_path_token(stripped)
        cleaned.append(token_norm)

    # Убираем дублирующиеся, ведущие и хвостовые флаги --new
    normalized: List[str] = []
    for t in cleaned:
        if t == "--new":
            if not normalized or normalized[-1] == "--new":
                continue
        normalized.append(t)

    while normalized and normalized[-1] == "--new":
        normalized.pop()

    return normalized


def join_bat_lines(content: str) -> List[str]:
    """
    Обрабатывает содержимое .bat/.cmd скрипта:
    - объединяет строки с символом продолжения ^
    - фильтрует комментарии (REM, ::) и команды оболочки (@echo, set, chcp и др.)
    """
    lines = content.splitlines()
    joined_lines: List[str] = []
    current_acc = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Пропускаем комментарии
        if stripped.startswith("::") or stripped.upper().startswith("REM ") or stripped.upper().startswith("@REM"):
            continue

        # Пропускаем стандартные служебные команды cmd
        upper = stripped.upper()
        if upper.startswith(("@ECHO", "CHCP", "CLS", "PAUSE", "EXIT", "TITLE", "CD ", "PUSHD ", "POPD ")):
            continue
        if upper.startswith("CALL SERVICE.BAT"):
            continue
        if upper.startswith("SET ") and "=" in stripped:
            # Служебные присвоения переменных cmd
            continue

        # Обработка символа продолжения строки ^
        if current_acc:
            current_acc += " " + stripped
        else:
            current_acc = stripped

        if current_acc.endswith("^"):
            current_acc = current_acc[:-1].rstrip()
        else:
            joined_lines.append(current_acc)
            current_acc = ""

    if current_acc:
        if current_acc.endswith("^"):
            current_acc = current_acc[:-1].rstrip()
        joined_lines.append(current_acc)

    return joined_lines


def _find_command_line(lines: List[str]) -> str:
    """Находит основную строку вызова winws/nfqws или блок аргументов."""
    for line in lines:
        lower = line.lower()
        if "winws" in lower or "nfqws" in lower or "--dpi-desync" in lower or "--filter-tcp" in lower or "--filter-udp" in lower:
            return line
    return lines[0] if lines else ""


def parse_bat_content(content: str, name: str = "") -> ParsedStrategy:
    """
    Парсит текст .bat/.cmd файла или строку аргументов winws/nfqws.
    """
    joined_lines = join_bat_lines(content)
    raw_cmd = _find_command_line(joined_lines)
    if not raw_cmd:
        raw_cmd = content.strip()

    # Токенизируем строку команды
    try:
        raw_tokens = shlex.split(raw_cmd)
    except Exception:
        # Fallback на простой split при некорректном экранировании
        raw_tokens = raw_cmd.split()

    # Отрезаем префикс запуска (start, title, /min, %BIN%winws.exe)
    start_idx = 0
    for idx, tok in enumerate(raw_tokens):
        if tok.startswith("--"):
            start_idx = idx
            break
    tokens = raw_tokens[start_idx:]

    # Извлекаем порты до очистки --wf-tcp / --wf-udp
    tcp_ports, udp_ports = extract_ports(tokens)

    # Очищаем аргументы от Windows флагов и адаптируем пути
    clean_arg_tokens = clean_tokens(tokens)

    # Формируем строку clean_args
    clean_args_str = " ".join(clean_arg_tokens)

    # Формируем список для exec (со снятыми внешними кавычками со значений)
    exec_args_list: List[str] = []
    for tok in clean_arg_tokens:
        if tok.startswith("--") and "=" in tok:
            k, v = tok.split("=", 1)
            exec_args_list.append(f"{k}={v.strip('\"')}")
        else:
            exec_args_list.append(tok)

    return ParsedStrategy(
        name=name or "parsed_strategy",
        tcp_ports=tcp_ports,
        udp_ports=udp_ports,
        clean_args=clean_args_str,
        clean_args_list=exec_args_list,
        raw_cmd=raw_cmd,
    )


def parse_bat_file(file_path: str) -> ParsedStrategy:
    """
    Читает и парсит .bat/.cmd файл стратегии.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Strategy file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    return parse_bat_content(content, name=base_name)


def parse_strategy_string(strategy_input: str, name: str = "") -> ParsedStrategy:
    """
    Универсальная точка входа: парсит путь к файлу или строку аргументов.
    """
    stripped = strategy_input.strip()
    if os.path.isfile(stripped) or stripped.lower().endswith((".bat", ".cmd")):
        if os.path.isfile(stripped):
            return parse_bat_file(stripped)

    return parse_bat_content(stripped, name=name)
