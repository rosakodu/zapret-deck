import os
import subprocess
import logging
import signal
import shutil
import shlex

try:
    from zapret_deck.bat_parser import parse_strategy_string, ParsedStrategy
    from zapret_deck.fakes_manager import FakesManager
    from zapret_deck.gamefilter import GameFilterManager
    from zapret_deck.diagnostics import check_nfqueue_status
except ImportError:
    from .bat_parser import parse_strategy_string, ParsedStrategy
    from .fakes_manager import FakesManager
    from .gamefilter import GameFilterManager
    from .diagnostics import check_nfqueue_status

logger = logging.getLogger("zapret-deck.zapret")

TABLE_NAME = "zapretunix"
CHAIN_NAME = "output"
QUEUE_NUM = 220
RULE_COMMENT = "Added by zapret-deck"

class ZapretManager:
    def __init__(self, plugin_dir: str, shared_dir: str = "/var/lib/zapret-deck"):
        self.plugin_dir = plugin_dir
        self.shared_dir = shared_dir
        self.bin_path = os.path.join(plugin_dir, "bin", "nfqws")
        self.log_file = os.path.join(plugin_dir, "zapret.log")
        self.fakes_manager = FakesManager(os.path.join(plugin_dir, "bin"), shared_dir=shared_dir)
        self.game_filter = GameFilterManager(enabled=True)

    def is_nfqueue_busy(self, queue_num: int = QUEUE_NUM) -> bool:
        """Проверяет, занята ли очередь NFQUEUE другим процессом."""
        status = check_nfqueue_status(queue_num)
        return status.get("is_busy", False)

    def cleanup_nfqueue(self, queue_num: int = QUEUE_NUM) -> bool:
        """Принудительно освобождает очередь NFQUEUE и завершает зависшие процессы."""
        logger.info(f"Cleaning up NFQUEUE {queue_num}...")
        status = check_nfqueue_status(queue_num)
        peer_pid = status.get("peer_pid")
        if peer_pid and peer_pid > 1:
            logger.info(f"Terminating queue holder process PID {peer_pid}")
            self._run_cmd(["kill", "-15", str(peer_pid)])
            self._run_cmd(["kill", "-9", str(peer_pid)])

        self._run_cmd(["pkill", "-9", "-f", self.bin_path])
        self._run_cmd(["pkill", "-9", "-f", f"nfqws.*{queue_num}"])
        self.clear_nftables()
        return not self.is_nfqueue_busy(queue_num)

    def ensure_queue_available(self, queue_num: int = QUEUE_NUM) -> bool:
        """Гарантирует доступность NFQUEUE перед стартом, выполняя автоочистку при занятости."""
        if self.is_nfqueue_busy(queue_num):
            logger.warning(f"NFQUEUE {queue_num} is occupied. Performing auto-cleanup...")
            return self.cleanup_nfqueue(queue_num)
        return True

    def _run_cmd(self, cmd: list) -> tuple:
        """Вспомогательный метод для запуска системных команд"""
        try:
            clean_env = os.environ.copy()
            clean_env.pop("LD_LIBRARY_PATH", None)
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=clean_env)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Failed to run command {' '.join(cmd)}: {e}")
            return -1, "", str(e)

    def is_running(self) -> bool:
        """Проверяет, запущен ли nfqws"""
        rc, stdout, _ = self._run_cmd(["pgrep", "-f", self.bin_path])
        return rc == 0 and bool(stdout)

    def clear_nftables(self):
        """Очищает правила в цепочке nftables, созданной плагином"""
        logger.info("Cleaning up nftables rules...")
        rc, stdout, _ = self._run_cmd(["nft", "list", "tables"])
        if f"inet {TABLE_NAME}" in stdout:
            self._run_cmd(["nft", "flush", "chain", "inet", TABLE_NAME, CHAIN_NAME])

    def destroy_nftables(self):
        """Полностью удаляет таблицу nftables при выгрузке плагина"""
        logger.info("Destroying nftables table...")
        rc, stdout, _ = self._run_cmd(["nft", "list", "tables"])
        if f"inet {TABLE_NAME}" in stdout:
            self._run_cmd(["nft", "delete", "table", "inet", TABLE_NAME])

    def _format_ports_nft(self, ports_str: str) -> str:
        # Преобразует порты "80,443" в формат nftables "{ 80, 443 }"
        ports_list = [p.strip() for p in ports_str.split(",") if p.strip()]
        if len(ports_list) == 1:
            return f"{{ {ports_list[0]} }}"
        return "{ " + ", ".join(ports_list) + " }"

    def setup_nftables(self, tcp_ports: str = "80,443", udp_ports: str = "443", enable_game_filter: bool = True):
        """Создает правила nftables для перенаправления HTTP/HTTPS/QUIC в nfqws"""
        logger.info(f"Setting up nftables rules for TCP: {tcp_ports}, UDP: {udp_ports}...")
        
        # 1. Создаем inet таблицу zapretunix (если её нет)
        rc, _, err = self._run_cmd(["nft", "add", "table", "inet", TABLE_NAME])
        if rc != 0:
            raise Exception(f"Failed to create nftables table: {err}")

        # 2. Создаем цепочку output (если её нет)
        rc, _, err = self._run_cmd([
            "nft", "add", "chain", "inet", TABLE_NAME, CHAIN_NAME,
            "{ type filter hook output priority 0 ; policy accept ; }"
        ])
        if rc != 0:
            raise Exception(f"Failed to create nftables chain: {err}")

        # 3. Очищаем старые правила в цепочке
        self.clear_nftables()

        # 4. GameFilter: добавляем accept bypass правило для игровых UDP портов перед NFQUEUE
        if enable_game_filter and self.game_filter and self.game_filter.is_enabled():
            game_ports = self.game_filter.get_nftables_ports()
            if game_ports:
                rc, _, err = self._run_cmd([
                    "nft", "add", "rule", "inet", TABLE_NAME, CHAIN_NAME,
                    "meta", "skuid", "!=", "nobody", "udp", "dport", game_ports, "counter", "accept",
                    "comment", '"zapret-deck-gamefilter-bypass"'
                ])
                if rc != 0:
                    logger.warning(f"Failed to add GameFilter bypass rule: {err}")

        # 5. Добавляем правило перенаправления TCP
        tcp_formatted = self._format_ports_nft(tcp_ports)
        rc, _, err = self._run_cmd([
            "nft", "add", "rule", "inet", TABLE_NAME, CHAIN_NAME,
            "meta", "skuid", "!=", "nobody", "tcp", "dport", tcp_formatted, "counter", "queue", "num", str(QUEUE_NUM), "bypass",
            "comment", f'"{RULE_COMMENT}"'
        ])
        if rc != 0:
            raise Exception(f"Failed to add TCP redirect rule: {err}")

        # 6. Добавляем правило перенаправления UDP
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
        self.ensure_queue_available(QUEUE_NUM)

        import shutil
        shared_dir = self.shared_dir
        shared_lists = os.path.join(shared_dir, "lists")
        shared_bin = os.path.join(shared_dir, "bin")

        try:
            # Создаем общие папки
            os.makedirs(shared_lists, exist_ok=True)
            os.makedirs(shared_bin, exist_ok=True)

            # 0. Гарантируем наличие активного Discord UDP фейка в bin плагина
            try:
                self.fakes_manager.ensure_active_fake()
            except Exception as fake_err:
                logger.warning(f"Failed to ensure active fake: {fake_err}")

            # 1. Копируем все файлы списков из локального плагина в общую папку
            local_lists_dir = os.path.join(self.plugin_dir, "lists")
            if os.path.exists(local_lists_dir):
                for filename in os.listdir(local_lists_dir):
                    src_file = os.path.join(local_lists_dir, filename)
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, os.path.join(shared_lists, filename))

            # 2. Копируем переданный хостлист (пользовательский или тестовый для автоподбора)
            if hostlist_file and os.path.exists(hostlist_file):
                shutil.copy2(hostlist_file, os.path.join(shared_lists, "list-general-user.txt"))
                logger.info(f"Copied hostlist {hostlist_file} to shared list-general-user.txt")

            # 3. Генерируем пустые заглушки для остальных списков пользователей
            user_lists = [
                "list-general-user.txt",
                "list-google-user.txt",
                "list-exclude-user.txt",
                "ipset-all-user.txt",
                "ipset-exclude-user.txt"
            ]
            for ul in user_lists:
                ul_path = os.path.join(shared_lists, ul)
                if not os.path.exists(ul_path):
                    with open(ul_path, "w") as f:
                        pass

            # 4. Копируем все .bin файлы (с фейковыми пакетами) из bin/ плагина в общую папку
            local_bin_dir = os.path.join(self.plugin_dir, "bin")
            if os.path.exists(local_bin_dir):
                for filename in os.listdir(local_bin_dir):
                    if filename.endswith(".bin"):
                        src_file = os.path.join(local_bin_dir, filename)
                        shutil.copy2(src_file, os.path.join(shared_bin, filename))

            # 5. Устанавливаем права 755 и владельца nobody, чтобы nfqws мог читать файлы
            self._run_cmd(["chmod", "-R", "755", shared_dir])
            self._run_cmd(["chown", "-R", "nobody:nobody", shared_dir])
        except Exception as e:
            logger.error(f"Failed to prepare shared directory: {e}")
            raise e

        # Парсим стратегию (поддерживаются .bat файлы, winws и nfqws строки)
        parsed = parse_strategy_string(strategy_args)
        tcp_ports = parsed.tcp_ports
        udp_ports = parsed.udp_ports

        filtered_args = []
        for arg in parsed.clean_args_list:
            # Заменяем плейсхолдеры на пути к ОБЩЕЙ папке, доступной для nobody
            arg_replaced = (
                arg.replace("%BIN%/", shared_bin + "/")
                .replace("%BIN%\\", shared_bin + "/")
                .replace("%BIN%", shared_bin + "/")
                .replace("%LISTS%/", shared_lists + "/")
                .replace("%LISTS%\\", shared_lists + "/")
                .replace("%LISTS%", shared_lists + "/")
            )
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
        """Останавливает nfqws и очищает nftables и NFQUEUE"""
        logger.info("Stopping zapret...")
        self.cleanup_nfqueue(QUEUE_NUM)
        logger.info("Zapret stopped and cleaned up")

    def parse_strategy(self, strategy_input: str) -> ParsedStrategy:
        """Парсит строку стратегии или .bat/.cmd файл."""
        return parse_strategy_string(strategy_input)

    def apply_bat_file(self, bat_path: str, hostlist_file: str = None):
        """Запускает nfqws напрямую из файла .bat стратегии."""
        parsed = parse_strategy_string(bat_path)
        return self.start(parsed.clean_args, hostlist_file=hostlist_file)
