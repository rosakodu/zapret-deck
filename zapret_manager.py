import os
import subprocess
import logging
import re
import shlex

logger = logging.getLogger("zapret-deck.zapret")

TABLE_NAME = "zapretunix"
CHAIN_NAME = "output"
QUEUE_NUM = 220
RULE_COMMENT = "Added by zapret-deck"

class ZapretManager:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.bin_path = os.path.join(plugin_dir, "bin", "nfqws")
        self.log_file = os.path.join(plugin_dir, "zapret.log")

    def _run_cmd(self, cmd: list) -> tuple:
        """Вспомогательный метод для запуска системных команд"""
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Failed to run command {' '.join(cmd)}: {e}")
            return -1, "", str(e)

    def is_running(self) -> bool:
        """Проверяет, запущен ли nfqws"""
        rc, stdout, _ = self._run_cmd(["pgrep", "-f", self.bin_path])
        return rc == 0 and bool(stdout)

    def clear_nftables(self):
        """Очищает правила nftables, созданные плагином"""
        logger.info("Cleaning up nftables rules...")
        
        # Проверяем, существует ли таблица
        rc, stdout, _ = self._run_cmd(["nft", "list", "tables"])
        if f"inet {TABLE_NAME}" not in stdout:
            logger.debug(f"Table {TABLE_NAME} does not exist, nothing to clean")
            return

        # Получаем handles правил с нашим комментарием
        rc, stdout, stderr = self._run_cmd(["nft", "-a", "list", "chain", "inet", TABLE_NAME, CHAIN_NAME])
        if rc == 0:
            for line in stdout.splitlines():
                if RULE_COMMENT in line:
                    # Строка вида: "... comment "Added by zapret-deck" handle 12"
                    parts = line.split()
                    if "handle" in parts:
                        handle_idx = parts.index("handle") + 1
                        if handle_idx < len(parts):
                            handle = parts[handle_idx]
                            logger.info(f"Deleting nftables rule handle {handle}")
                            self._run_cmd(["nft", "delete", "rule", "inet", TABLE_NAME, CHAIN_NAME, "handle", handle])

        # Пытаемся удалить цепочку и таблицу (если они пустые)
        self._run_cmd(["nft", "delete", "chain", "inet", TABLE_NAME, CHAIN_NAME])
        self._run_cmd(["nft", "delete", "table", "inet", TABLE_NAME])

    def setup_nftables(self, tcp_ports: str = "80,443", udp_ports: str = "443"):
        """Создает правила nftables для перенаправления TCP/UDP в nfqws"""
        logger.info(f"Setting up nftables rules (TCP: {tcp_ports}, UDP: {udp_ports})...")
        self.clear_nftables()

        # Форматируем порты для nftables (заменяем запятые на пробелы и запятые)
        nft_tcp = tcp_ports.replace(",", ", ")
        nft_udp = udp_ports.replace(",", ", ")

        # 1. Создаем inet таблицу zapretunix
        rc, _, err = self._run_cmd(["nft", "add", "table", "inet", TABLE_NAME])
        if rc != 0:
            raise Exception(f"Failed to create nftables table: {err}")

        # 2. Создаем цепочку output
        rc, _, err = self._run_cmd([
            "nft", "add", "chain", "inet", TABLE_NAME, CHAIN_NAME,
            "{ type filter hook output priority 0 ; policy accept ; }"
        ])
        if rc != 0:
            raise Exception(f"Failed to create nftables chain: {err}")

        # 3. Добавляем правило перенаправления TCP
        rc, _, err = self._run_cmd([
            "nft", "add", "rule", "inet", TABLE_NAME, CHAIN_NAME,
            "tcp", "dport", f"{{ {nft_tcp} }}", "counter", "queue", "num", str(QUEUE_NUM), "bypass",
            "comment", f'"{RULE_COMMENT}"'
        ])
        if rc != 0:
            raise Exception(f"Failed to add TCP redirect rule: {err}")

        # 4. Добавляем правило перенаправления UDP
        rc, _, err = self._run_cmd([
            "nft", "add", "rule", "inet", TABLE_NAME, CHAIN_NAME,
            "udp", "dport", f"{{ {nft_udp} }}", "counter", "queue", "num", str(QUEUE_NUM), "bypass",
            "comment", f'"{RULE_COMMENT}"'
        ])
        if rc != 0:
            raise Exception(f"Failed to add UDP redirect rule: {err}")

    def start(self, strategy_args: str, user_hostlist_path: str = None):
        """Запускает nfqws с выбранной стратегией"""
        logger.info(f"Starting zapret (nfqws) with strategy args: {strategy_args}")
        self.stop()

        # Создаем необходимые директории
        lists_dir = os.path.join(self.plugin_dir, "lists")
        os.makedirs(lists_dir, exist_ok=True)

        # Гарантируем наличие пользовательских файлов (хотя бы пустых), чтобы nfqws не падал
        user_files = [
            "list-general-user.txt",
            "list-exclude-user.txt",
            "ipset-exclude-user.txt"
        ]
        for uf in user_files:
            uf_path = os.path.join(lists_dir, uf)
            if not os.path.exists(uf_path):
                with open(uf_path, "w") as f:
                    f.write("")

        # Если передан пользовательский хостлист, копируем его в list-general-user.txt
        if user_hostlist_path and os.path.exists(user_hostlist_path):
            try:
                import shutil
                shutil.copy(user_hostlist_path, os.path.join(lists_dir, "list-general-user.txt"))
                logger.info("Copied user hostlist to list-general-user.txt")
            except Exception as e:
                logger.error(f"Failed to copy user hostlist: {e}")

        # Извлекаем порты для nftables
        tcp_ports_match = re.search(r'--wf-tcp=([0-9,-]+)', strategy_args)
        udp_ports_match = re.search(r'--wf-udp=([0-9,-]+)', strategy_args)

        tcp_ports = tcp_ports_match.group(1) if tcp_ports_match else "80,443"
        udp_ports = udp_ports_match.group(1) if udp_ports_match else "443"

        # Очищаем аргументы от --wf-tcp и --wf-udp для nfqws
        clean_args = re.sub(r'--wf-tcp=[^\s]+', '', strategy_args)
        clean_args = re.sub(r'--wf-udp=[^\s]+', '', clean_args)

        # Заменяем плейсхолдеры путей
        bin_dir = os.path.join(self.plugin_dir, "bin") + "/"
        clean_args = clean_args.replace("%BIN%", bin_dir).replace("%LISTS%", lists_dir + "/")

        # Создаем nftables правила для извлеченных портов
        self.setup_nftables(tcp_ports, udp_ports)

        # Парсим аргументы
        args = [
            self.bin_path,
            f"--qnum={QUEUE_NUM}",
            "--daemon"
        ]
        args.extend(shlex.split(clean_args))

        try:
            logger.info(f"Executing: {' '.join(args)}")
            # Запускаем в фоновом режиме
            with open(self.log_file, "a") as log:
                subprocess.Popen(
                    args,
                    stdout=log,
                    stderr=log,
                    start_new_session=True
                )
            logger.info("Zapret (nfqws) started successfully")
        except Exception as e:
            self.clear_nftables()
            logger.error(f"Failed to start nfqws: {e}")
            raise e

    def stop(self):
        """Останавливает nfqws и очищает nftables"""
        logger.info("Stopping zapret...")
        
        # Убиваем процессы nfqws
        self._run_cmd(["pkill", "-f", self.bin_path])
        
        # На всякий случай жестко убиваем
        rc, stdout, _ = self._run_cmd(["pgrep", "-f", self.bin_path])
        if stdout:
            self._run_cmd(["pkill", "-9", "-f", self.bin_path])

        # Очищаем nftables
        self.clear_nftables()
        logger.info("Zapret stopped and cleaned up")
