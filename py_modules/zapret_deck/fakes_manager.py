"""
fakes_manager.py - Management and updates for binary fake packets (.bin) in zapret-deck.
Handles Discord UDP fakes, active fake payload selection, integrity checks, and GameFilter.
"""

import os
import shutil
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("zapret-deck.fakes")

ACTIVE_DISCORD_FAKE_NAME = "ACTIVE_DISCORD_UDP.bin"
DEFAULT_DISCORD_FAKE_SOURCE = "quic_initial_dbankcloud_ru.bin"
SHARED_BASE_DIR = "/var/lib/zapret-deck"

# Standard ports used for Discord voice / game filter UDP traffic
GAME_FILTER_UDP_PORTS = "19294-19344,50000-50100"
GAME_FILTER_TCP_PORTS = "2053,2083,2087,2096,8443"


def compute_file_sha256(filepath: str) -> str:
    """Вычисляет хэш SHA256 для файла."""
    if not os.path.isfile(filepath):
        return ""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class FakesManager:
    """Менеджер бинарных фейков (.bin) для zapret-deck."""

    def __init__(self, bin_dir: Optional[str] = None, shared_dir: str = SHARED_BASE_DIR):
        if bin_dir is None:
            # По умолчанию берем bin из корневой структуры плагина
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bin_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "bin"))

        self.bin_dir = bin_dir
        self.shared_dir = shared_dir
        self.shared_bin_dir = os.path.join(shared_dir, "bin")

    def _sync_file_to_shared(self, src_path: str, filename: str):
        """Копирует файл в shared_bin_dir, если каталог доступен для записи."""
        try:
            if os.path.exists(self.shared_bin_dir) and os.access(self.shared_bin_dir, os.W_OK):
                dst_path = os.path.join(self.shared_bin_dir, filename)
                shutil.copy2(src_path, dst_path)
                logger.debug(f"Synced {filename} to shared bin directory")
        except Exception as e:
            logger.warning(f"Could not sync {filename} to shared dir: {e}")

    def list_available_fakes(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех доступных .bin файлов в bin_dir с хэшами
        и флагом активности для Discord UDP.
        """
        if not os.path.exists(self.bin_dir):
            return []

        active_path = os.path.join(self.bin_dir, ACTIVE_DISCORD_FAKE_NAME)
        active_hash = compute_file_sha256(active_path) if os.path.isfile(active_path) else ""

        fakes: List[Dict[str, Any]] = []
        for filename in sorted(os.listdir(self.bin_dir)):
            if filename.endswith(".bin") and filename != ACTIVE_DISCORD_FAKE_NAME:
                file_path = os.path.join(self.bin_dir, filename)
                if os.path.isfile(file_path):
                    f_hash = compute_file_sha256(file_path)
                    fakes.append({
                        "name": filename,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "sha256": f_hash,
                        "is_active": (bool(active_hash) and f_hash == active_hash),
                    })

        return fakes

    def get_active_fake(self) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о текущем активном фейке Discord UDP."""
        active_path = os.path.join(self.bin_dir, ACTIVE_DISCORD_FAKE_NAME)
        if not os.path.isfile(active_path):
            return None

        active_hash = compute_file_sha256(active_path)
        matched_source = None
        for fake in self.list_available_fakes():
            if fake["sha256"] == active_hash:
                matched_source = fake["name"]
                break

        return {
            "name": ACTIVE_DISCORD_FAKE_NAME,
            "path": active_path,
            "size": os.path.getsize(active_path),
            "sha256": active_hash,
            "matched_source": matched_source,
        }

    def set_active_fake(self, fake_name: str) -> bool:
        """
        Устанавливает указанный .bin файл в качестве ACTIVE_DISCORD_UDP.bin.
        Копирует файл в bin_dir и shared_bin_dir.
        """
        src_path = os.path.join(self.bin_dir, fake_name)
        if not os.path.isfile(src_path):
            logger.error(f"Cannot set active fake: source file not found {src_path}")
            return False

        dst_path = os.path.join(self.bin_dir, ACTIVE_DISCORD_FAKE_NAME)
        shutil.copy2(src_path, dst_path)
        self._sync_file_to_shared(dst_path, ACTIVE_DISCORD_FAKE_NAME)
        logger.info(f"Set active Discord UDP fake to: {fake_name}")
        return True

    def ensure_active_fake(self, default_source: str = DEFAULT_DISCORD_FAKE_SOURCE) -> str:
        """
        Гарантирует существование ACTIVE_DISCORD_UDP.bin.
        Если отсутствует, инициализирует его из default_source.
        """
        os.makedirs(self.bin_dir, exist_ok=True)
        active_path = os.path.join(self.bin_dir, ACTIVE_DISCORD_FAKE_NAME)

        if not os.path.isfile(active_path):
            src_path = os.path.join(self.bin_dir, default_source)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, active_path)
                logger.info(f"Initialized {ACTIVE_DISCORD_FAKE_NAME} from {default_source}")
            else:
                # Ищем любой доступный .bin файл
                candidates = [f for f in os.listdir(self.bin_dir) if f.endswith(".bin") and f != ACTIVE_DISCORD_FAKE_NAME]
                if candidates:
                    fallback_source = candidates[0]
                    shutil.copy2(os.path.join(self.bin_dir, fallback_source), active_path)
                    logger.info(f"Initialized {ACTIVE_DISCORD_FAKE_NAME} from fallback {fallback_source}")
                else:
                    # Создаем минимальную заглушку для тестов
                    with open(active_path, "wb") as f:
                        f.write(b"\x00" * 32)
                    logger.warning(f"Created minimal stub for {ACTIVE_DISCORD_FAKE_NAME}")

        self._sync_file_to_shared(active_path, ACTIVE_DISCORD_FAKE_NAME)
        return active_path

    def install_fake_from_bytes(self, filename: str, data: bytes, set_as_active: bool = False) -> str:
        """Сохраняет бинарный фейк из байтов."""
        if not filename.endswith(".bin"):
            filename += ".bin"

        os.makedirs(self.bin_dir, exist_ok=True)
        target_path = os.path.join(self.bin_dir, filename)
        with open(target_path, "wb") as f:
            f.write(data)

        self._sync_file_to_shared(target_path, filename)

        if set_as_active:
            self.set_active_fake(filename)

        logger.info(f"Installed fake payload: {filename} ({len(data)} bytes)")
        return target_path

    def download_fake(self, url: str, target_filename: Optional[str] = None, timeout: int = 10) -> Optional[str]:
        """Загружает бинарный фейк по сетевому URL."""
        import urllib.request

        if not target_filename:
            target_filename = os.path.basename(url.split("?")[0])
            if not target_filename.endswith(".bin"):
                target_filename = "downloaded_fake.bin"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "zapret-deck/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            return self.install_fake_from_bytes(target_filename, data)
        except Exception as e:
            logger.error(f"Failed to download fake from {url}: {e}")
            return None

    @staticmethod
    def get_game_filter_ports() -> Dict[str, str]:
        """Возвращает диапазоны портов GameFilter."""
        return {
            "tcp": GAME_FILTER_TCP_PORTS,
            "udp": GAME_FILTER_UDP_PORTS,
        }
