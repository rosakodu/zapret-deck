"""
gamefilter.py - Protection of online game UDP traffic from DPI desynchronization.
Provides presets for Steam, Source, Blizzard, Riot, EA, Epic, and P2P ports.
Generates nftables bypass rules so game UDP packets bypass NFQUEUE.
"""

import re
import logging
from typing import List, Dict, Tuple, Any, Optional

logger = logging.getLogger("zapret-deck.gamefilter")

# Predefined game port presets (UDP)
DEFAULT_GAME_PRESETS: Dict[str, List[str]] = {
    "steam": ["27000-27100", "3478", "4379-4380"],
    "source_cs2": ["27015-27030", "27005"],
    "riot": ["5000-5500", "8393-8400"],
    "blizzard": ["1119", "3724", "6112-6114"],
    "ea_apex": ["1024-1124", "18000", "18060", "18120", "37005", "39698-39699", "44015"],
    "epic_fortnite": ["7777-7780", "9000-9999"],
    "genshin": ["22101-22102"],
    "console_p2p": ["3074", "3075", "3076", "3478-3479"],
}


def parse_port_entry(entry: str) -> Optional[Tuple[int, int]]:
    """Парсит одиночный порт или диапазон 'start-end' в кортеж (start, end)."""
    entry = entry.strip()
    if not entry:
        return None
    if "-" in entry:
        parts = entry.split("-", 1)
        try:
            start, end = int(parts[0].strip()), int(parts[1].strip())
            if 1 <= start <= end <= 65535:
                return (start, end)
        except ValueError:
            return None
    else:
        try:
            val = int(entry)
            if 1 <= val <= 65535:
                return (val, val)
        except ValueError:
            return None
    return None


def parse_ports_string(ports_str: str) -> List[Tuple[int, int]]:
    """Парсит строку портов ('80,443,27000-27050') в список кортежей (start, end)."""
    ranges: List[Tuple[int, int]] = []
    for item in ports_str.split(","):
        parsed = parse_port_entry(item)
        if parsed:
            ranges.append(parsed)
    return ranges


def is_port_in_ranges(port: int, ranges: List[Tuple[int, int]]) -> bool:
    """Проверяет, входит ли порт в один из заданных диапазонов."""
    for start, end in ranges:
        if start <= port <= end:
            return True
    return False


def exclude_ports_from_string(ports_str: str, exclude_ranges: List[Tuple[int, int]]) -> str:
    """
    Исключает диапазоны портов из исходной строки портов.
    Возвращает строку с оставшимися портами.
    """
    remaining: List[str] = []
    for item in ports_str.split(","):
        parsed = parse_port_entry(item)
        if not parsed:
            continue
        start, end = parsed
        # Если диапазон полностью внутри исключаемых - отбрасываем
        if is_port_in_ranges(start, exclude_ranges) and is_port_in_ranges(end, exclude_ranges):
            continue
        # Если одиночный порт совпал
        if start == end and is_port_in_ranges(start, exclude_ranges):
            continue
        remaining.append(item.strip())
    return ",".join(remaining)


class GameFilterManager:
    """Менеджер правил GameFilter для защиты игрового UDP трафика."""

    def __init__(self, enabled: bool = True):
        self.enabled: bool = enabled
        self.preset_states: Dict[str, bool] = {name: True for name in DEFAULT_GAME_PRESETS}
        self.custom_ports: List[str] = []

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def set_preset_state(self, preset_name: str, active: bool) -> None:
        if preset_name in self.preset_states:
            self.preset_states[preset_name] = bool(active)

    def add_custom_port(self, port_or_range: str) -> bool:
        """Добавляет пользовательский порт или диапазон."""
        parsed = parse_port_entry(port_or_range)
        if parsed and port_or_range.strip() not in self.custom_ports:
            self.custom_ports.append(port_or_range.strip())
            return True
        return False

    def remove_custom_port(self, port_or_range: str) -> bool:
        """Удаляет пользовательский порт."""
        item = port_or_range.strip()
        if item in self.custom_ports:
            self.custom_ports.remove(item)
            return True
        return False

    def get_protected_port_specs(self) -> List[str]:
        """Возвращает список всех активных спецификаций портов (из пресетов и custom)."""
        specs: List[str] = []
        for name, is_active in self.preset_states.items():
            if is_active and name in DEFAULT_GAME_PRESETS:
                specs.extend(DEFAULT_GAME_PRESETS[name])
        for cp in self.custom_ports:
            if cp not in specs:
                specs.append(cp)
        return specs

    def get_parsed_ranges(self) -> List[Tuple[int, int]]:
        """Возвращает список диапазонов (start, end) для всех защищенных портов."""
        ranges: List[Tuple[int, int]] = []
        for spec in self.get_protected_port_specs():
            parsed = parse_port_entry(spec)
            if parsed:
                ranges.append(parsed)
        return ranges

    def is_game_port(self, port: int) -> bool:
        """Проверяет, относится ли данный порт к защищенным игровым портам."""
        if not self.enabled:
            return False
        return is_port_in_ranges(port, self.get_parsed_ranges())

    def filter_udp_ports(self, udp_ports_str: str) -> str:
        """Исключает защищенные игровые порты из строки UDP портов nfqws."""
        if not self.enabled:
            return udp_ports_str
        return exclude_ports_from_string(udp_ports_str, self.get_parsed_ranges())

    def get_nftables_ports(self) -> str:
        """Форматирует активные игровые порты для nftables: '{ 27000-27100, 3478 }'."""
        specs = self.get_protected_port_specs()
        if not specs:
            return ""
        if len(specs) == 1:
            return f"{{ {specs[0]} }}"
        return "{ " + ", ".join(specs) + " }"

    def to_dict(self) -> Dict[str, Any]:
        """Экспорт настроек в словарь для сериализации."""
        return {
            "enabled": self.enabled,
            "preset_states": dict(self.preset_states),
            "custom_ports": list(self.custom_ports),
            "protected_specs_count": len(self.get_protected_port_specs()),
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Загрузка настроек из словаря."""
        if not isinstance(data, dict):
            return
        if "enabled" in data:
            self.enabled = bool(data["enabled"])
        if "preset_states" in data and isinstance(data["preset_states"], dict):
            for k, v in data["preset_states"].items():
                if k in self.preset_states:
                    self.preset_states[k] = bool(v)
        if "custom_ports" in data and isinstance(data["custom_ports"], list):
            self.custom_ports = [str(p) for p in data["custom_ports"] if parse_port_entry(str(p))]
