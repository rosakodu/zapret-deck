import os
import subprocess
import logging
import signal

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

    def _format_ports_nft(self, ports_str: str) -> str:
        # Преобразует порты "80,443" в формат nftables "{ 80, 443 }"
        ports_list = [p.strip() for p in ports_str.split(",") if p.strip()]
        if len(ports_list) == 1:
            return f"{{ {ports_list[0]} }}"
        return "{ " + ", ".join(ports_list) + " }"

    def setup_nftables(self, tcp_ports: str = "80,443", udp_ports: str = "443"):
        """Создает правила nftables для перенаправления HTTP/HTTPS/QUIC в nfqws"""
        logger.info(f"Setting up nftables rules for TCP: {tcp_ports}, UDP: {udp_ports}...")
        self.clear_nftables()

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
        tcp_formatted = self._format_ports_nft(tcp_ports)
        rc, _, err = self._run_cmd([
            "nft", "add", "rule", "inet", TABLE_NAME, CHAIN_NAME,
            "meta", "skuid", "!=", "nobody", "tcp", "dport", tcp_formatted, "counter", "queue", "num", str(QUEUE_NUM), "bypass",
            "comment", f'"{RULE_COMMENT}"'
        ])
        if rc != 0:
            raise Exception(f"Failed to add TCP redirect rule: {err}")

        # 4. Добавляем правило перенаправления UDP
        udp_formatted = self._format_ports_nft(udp_ports)
        rc, _, err = self._run_cmd([
            "nft", "add", "rule", "inet", TABLE_NAME, CHAIN_NAME,
            "meta", "skuid", "!=", "nobody", "udp", "dport", udp_formatted, "counter", "queue", "num", str(QUEUE_NUM), "bypass",
            "comment", f'"{RULE_COMMENT}"'
        ])
        if rc != 0:
            raise Exception(f"Failed to add UDP redirect rule: {err}")

    def start(self, strategy_args: str, hostlist_file: str = None):
        """Запускает nfqws с выбранной стратегией"""
        logger.info(f"Starting zapret (nfqws) with strategy args: {strategy_args}")
        self.stop()

        lists_dir = os.path.join(self.plugin_dir, "lists")
        os.makedirs(lists_dir, exist_ok=True)

        # Копируем пользовательский список доменов, если он передан
        if hostlist_file and os.path.exists(hostlist_file):
            import shutil
            try:
                shutil.copy(hostlist_file, os.path.join(lists_dir, "list-general-user.txt"))
                logger.info(f"Copied user hostlist {hostlist_file} to list-general-user.txt")
            except Exception as e:
                logger.error(f"Failed to copy user hostlist: {e}")

        # Генерируем пустые заглушки для остальных пользовательских списков
        user_lists = [
            "list-general-user.txt",
            "list-google-user.txt",
            "list-exclude-user.txt",
            "ipset-all-user.txt",
            "ipset-exclude-user.txt"
        ]
        for ul in user_lists:
            ul_path = os.path.join(lists_dir, ul)
            if not os.path.exists(ul_path):
                with open(ul_path, "w") as f:
                    pass

        # Парсим порты и отфильтровываем аргументы
        tcp_ports = "80,443"
        udp_ports = "443"
        
        import shlex
        strat_args = shlex.split(strategy_args)
        
        filtered_args = []
        for arg in strat_args:
            # Заменяем плейсхолдеры путей на абсолютные пути Steam Deck с разделителем
            arg_replaced = arg.replace("%BIN%", os.path.join(self.plugin_dir, "bin") + "/").replace("%LISTS%", os.path.join(self.plugin_dir, "lists") + "/")
            
            if arg.startswith("--wf-tcp="):
                tcp_ports = arg.split("=")[1]
            elif arg.startswith("--wf-udp="):
                udp_ports = arg.split("=")[1]
            else:
                filtered_args.append(arg_replaced)

        # 1. Создаем nftables правила перед стартом демона
        self.setup_nftables(tcp_ports, udp_ports)

        # 2. Формируем финальные аргументы nfqws
        args = [
            self.bin_path,
            f"--qnum={QUEUE_NUM}",
            "--daemon",
            "--user=nobody"
        ]
        args.extend(filtered_args)

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
