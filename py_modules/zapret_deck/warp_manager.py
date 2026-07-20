import os
import subprocess
import logging
import time
import shutil

logger = logging.getLogger("zapret-deck.warp")

class WarpManager:
    def __init__(self, plugin_dir: str, settings_dir: str):
        self.plugin_dir = plugin_dir
        self.settings_dir = settings_dir
        self.bin_path = os.path.join(plugin_dir, "bin", "usque")
        self.config_path = os.path.join(settings_dir, "warp_config.json")
        self.log_file = os.path.join(plugin_dir, "warp.log")
        
        self.interface_name = "warp0"
        self.scripts_dir = os.path.join(settings_dir, "scripts")
        self.up_script_path = os.path.join(self.scripts_dir, "warp_up.sh")
        self.down_script_path = os.path.join(self.scripts_dir, "warp_down.sh")
        
        os.makedirs(self.scripts_dir, exist_ok=True)
        os.makedirs(self.settings_dir, exist_ok=True)

    def _run_cmd(self, cmd: list) -> tuple:
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Failed to run command {' '.join(cmd)}: {e}")
            return -1, "", str(e)

    def is_registered(self) -> bool:
        """Проверяет наличие конфига WARP"""
        return os.path.exists(self.config_path)

    def register(self) -> bool:
        """Регистрирует новый аккаунт WARP"""
        logger.info("Registering new WARP client...")
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except OSError:
                pass
                
        cmd = [
            self.bin_path,
            "register",
            "--accept-tos",
            "-c", self.config_path
        ]
        
        rc, out, err = self._run_cmd(cmd)
        if rc == 0 and os.path.exists(self.config_path):
            logger.info("WARP registered successfully")
            return True
        else:
            logger.error(f"Failed to register WARP: rc={rc}, out={out}, err={err}")
            return False

    def is_running(self) -> bool:
        """Проверяет, запущен ли процесс usque nativetun"""
        rc, stdout, _ = self._run_cmd(["pgrep", "-f", f"usque nativetun"])
        return rc == 0 and bool(stdout)

    def _write_routing_scripts(self):
        """Создает скрипты для настройки маршрутизации и DNS"""
        resolv_conf = "/etc/resolv.conf"
        resolv_bak = "/etc/resolv.conf.bak"
        
        # Скрипт UP (вызывается при подключении)
        up_content = f"""#!/bin/bash
logger -t "zapret-deck-warp" "Tunnel interface UP: $USQUE_IFACE, endpoint: $USQUE_ENDPOINT"

# 1. Получаем текущий шлюз по умолчанию и интерфейс
GW=$(ip route show | grep default | awk '{{print $3}}' | head -n1)
DEV=$(ip route show | grep default | awk '{{print $5}}' | head -n1)

if [ -n "$GW" ] && [ -n "$DEV" ]; then
    logger -t "zapret-deck-warp" "Current default gateway: $GW on device $DEV"
    # Добавляем маршрут до самого сервера WARP через текущий шлюз, чтобы туннель не упал
    ip route add "$USQUE_ENDPOINT" via "$GW" dev "$DEV" 2>/dev/null || true
else
    logger -t "zapret-deck-warp" "Could not find default gateway"
fi

# 2. Перенаправляем весь трафик в TUN-интерфейс с помощью двух маршрутов (def1 трюк)
ip route add 0.0.0.0/1 dev "$USQUE_IFACE" 2>/dev/null || true
ip route add 128.0.0.0/1 dev "$USQUE_IFACE" 2>/dev/null || true

# 3. Подменяем DNS на Cloudflare DNS
if [ -f "{resolv_conf}" ] && [ ! -f "{resolv_bak}" ]; then
    cp "{resolv_conf}" "{resolv_bak}"
    echo -e "nameserver 1.1.1.1\\nnameserver 1.0.0.1" > "{resolv_conf}"
    logger -t "zapret-deck-warp" "DNS updated to 1.1.1.1"
fi
"""

        # Скрипт DOWN (вызывается при отключении)
        down_content = f"""#!/bin/bash
logger -t "zapret-deck-warp" "Tunnel interface DOWN: $USQUE_IFACE"

# 1. Удаляем маршруты
ip route del "$USQUE_ENDPOINT" 2>/dev/null || true
ip route del 0.0.0.0/1 dev "$USQUE_IFACE" 2>/dev/null || true
ip route del 128.0.0.0/1 dev "$USQUE_IFACE" 2>/dev/null || true

# 2. Восстанавливаем оригинальный DNS
if [ -f "{resolv_bak}" ]; then
    mv -f "{resolv_bak}" "{resolv_conf}"
    logger -t "zapret-deck-warp" "DNS restored from backup"
fi
"""

        with open(self.up_script_path, "w") as f:
            f.write(up_content)
        os.chmod(self.up_script_path, 0o755)
        
        with open(self.down_script_path, "w") as f:
            f.write(down_content)
        os.chmod(self.down_script_path, 0o755)
        
        logger.debug("Routing scripts written and made executable")

    def cleanup_network(self):
        """Аварийное восстановление сети при старте плагина или сбоях"""
        logger.info("Performing network routing and DNS emergency cleanup...")
        
        # 1. Удаляем маршруты
        # Находим имя интерфейса в таблице маршрутов
        rc, stdout, _ = self._run_cmd(["ip", "route", "show"])
        for line in stdout.splitlines():
            if self.interface_name in line:
                self._run_cmd(["ip", "route", "del", "0.0.0.0/1", "dev", self.interface_name])
                self._run_cmd(["ip", "route", "del", "128.0.0.0/1", "dev", self.interface_name])
                
        # Пытаемся удалить интерфейс
        self._run_cmd(["ip", "link", "delete", self.interface_name])

        # 2. Восстанавливаем оригинальный resolv.conf если остался бэкап
        resolv_conf = "/etc/resolv.conf"
        resolv_bak = "/etc/resolv.conf.bak"
        if os.path.exists(resolv_bak):
            try:
                shutil.move(resolv_bak, resolv_conf)
                logger.info("Restored original resolv.conf from backup")
            except Exception as e:
                logger.error(f"Failed to restore resolv.conf: {e}")

    def start(self) -> bool:
        """Запускает usque nativetun"""
        logger.info("Starting WARP (usque)...")
        if not self.is_registered():
            logger.error("WARP is not registered, cannot start")
            return False
            
        self.stop()
        
        # Заново пишем скрипты
        self._write_routing_scripts()

        cmd = [
            self.bin_path,
            "nativetun",
            "-c", self.config_path,
            "--interface-name", self.interface_name,
            "--on-connect", self.up_script_path,
            "--on-disconnect", self.down_script_path
        ]

        try:
            logger.info(f"Executing: {' '.join(cmd)}")
            with open(self.log_file, "a") as log:
                subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=log,
                    start_new_session=True
                )
            
            # Даем туннелю 3 секунды на установление соединения
            time.sleep(3)
            if self.is_running():
                logger.info("WARP (usque) started successfully")
                return True
            else:
                logger.error("WARP process died immediately after startup")
                self.cleanup_network()
                return False
        except Exception as e:
            logger.error(f"Failed to start WARP: {e}")
            self.cleanup_network()
            return False

    def stop(self):
        """Останавливает usque nativetun и чистит маршруты"""
        logger.info("Stopping WARP...")
        
        # Убиваем процесс usque nativetun
        self._run_cmd(["pkill", "-f", f"usque nativetun"])
        
        # Ждем немного
        time.sleep(1)
        
        # Если кто-то остался
        rc, stdout, _ = self._run_cmd(["pgrep", "-f", f"usque nativetun"])
        if stdout:
            self._run_cmd(["pkill", "-9", "-f", f"usque nativetun"])

        # Вызываем аварийную очистку сети
        self.cleanup_network()
        logger.info("WARP stopped and network cleaned up")
