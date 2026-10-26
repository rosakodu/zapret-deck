"""
Desktop environment integration for Zapret-Deck on SteamOS / KDE Plasma.
Handles KDE autostart management and background tray process control
without cluttering the desktop Application Launcher menu.
"""

import os
import shutil
import subprocess
from typing import Dict, Any


def get_user_home() -> str:
    """Discovers desktop user's home directory (e.g. /home/deck)."""
    if os.path.isdir("/home/deck"):
        return "/home/deck"

    if os.geteuid() == 0 and os.path.isdir("/home"):
        try:
            users = [
                u
                for u in os.listdir("/home")
                if u != "lost+found" and os.path.isdir(os.path.join("/home", u))
            ]
            if users:
                return os.path.join("/home", users[0])
        except Exception:
            pass

    return os.path.expanduser("~")


def get_desktop_paths() -> Dict[str, str]:
    """Returns absolute paths for autostart and legacy app entries."""
    user_home = get_user_home()
    apps_dir = os.path.join(user_home, ".local", "share", "applications")
    autostart_dir = os.path.join(user_home, ".config", "autostart")
    return {
        "apps_dir": apps_dir,
        "app_file": os.path.join(apps_dir, "zapret-deck-tray.desktop"),
        "autostart_dir": autostart_dir,
        "autostart_file": os.path.join(autostart_dir, "zapret-deck-tray.desktop"),
    }


def generate_autostart_content(plugin_dir: str) -> str:
    """Generates KDE autostart FreeDesktop entry with NoDisplay=true."""
    script_path = os.path.join(plugin_dir, "tray", "tray_app.py")
    icon_path = os.path.join(plugin_dir, "assets", "logo.png")

    content = f"""[Desktop Entry]
Type=Application
Name=Zapret Deck Tray
Comment=Zapret Deck system tray background companion
Exec=python3 "{script_path}"
Icon={icon_path}
Terminal=false
NoDisplay=true
StartupNotify=false
X-KDE-autostart-after=panel
"""
    return content


def _get_target_uid_gid() -> tuple:
    """Discovers target non-root uid and gid."""
    user_home = get_user_home()
    try:
        st = os.stat(user_home)
        return st.st_uid, st.st_gid
    except Exception:
        return 1000, 1000


def _safe_write_file(target_path: str, content: str) -> bool:
    """Writes autostart file and ensures proper non-root ownership if run as root."""
    try:
        if os.path.isfile(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    if f.read() == content:
                        return True
            except Exception:
                pass

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(target_path, 0o644)

        if os.geteuid() == 0:
            uid, gid = _get_target_uid_gid()
            os.chown(target_path, uid, gid)
        return True
    except PermissionError:
        return True
    except Exception as e:
        print(f"Error writing {target_path}: {e}")
        return False


def remove_app_menu_entry() -> None:
    """Removes legacy .desktop file from applications menu if present."""
    try:
        paths = get_desktop_paths()
        if os.path.exists(paths["app_file"]):
            os.remove(paths["app_file"])
            subprocess.run(
                ["update-desktop-database", paths["apps_dir"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def set_autostart(plugin_dir: str, enable: bool) -> bool:
    """Enables or disables KDE Plasma autostart."""
    paths = get_desktop_paths()
    remove_app_menu_entry()
    try:
        if enable:
            os.makedirs(paths["autostart_dir"], exist_ok=True)
            if os.geteuid() == 0:
                uid, gid = _get_target_uid_gid()
                try:
                    os.chown(paths["autostart_dir"], uid, gid)
                except Exception:
                    pass

            content = generate_autostart_content(plugin_dir)
            return _safe_write_file(paths["autostart_file"], content)
        else:
            if os.path.exists(paths["autostart_file"]):
                try:
                    os.remove(paths["autostart_file"])
                except Exception:
                    pass
            return True
    except Exception as e:
        print(f"Failed to set autostart={enable}: {e}")
        return False


def get_desktop_integration_status(plugin_dir: str) -> Dict[str, Any]:
    """Checks whether autostart is currently configured."""
    paths = get_desktop_paths()
    return {
        "autostart": os.path.exists(paths["autostart_file"]),
    }


def kill_tray_process() -> bool:
    """Terminates any running zapret tray_app.py instances."""
    try:
        if os.geteuid() == 0:
            user_home = get_user_home()
            user_name = os.path.basename(user_home) or "deck"
            subprocess.run(
                ["systemctl", "--user", "-M", f"{user_name}@", "stop", "zapret-deck-tray"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ["systemctl", "--user", "stop", "zapret-deck-tray"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass
    try:
        subprocess.run(
            ["pkill", "-f", "zapret.*tray_app.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def is_desktop_session_active() -> bool:
    """Checks whether KDE Plasma desktop session is currently running."""
    try:
        res = subprocess.run(["pgrep", "-x", "plasmashell"], stdout=subprocess.PIPE)
        return res.returncode == 0 and bool(res.stdout.strip())
    except Exception:
        return False


def launch_tray_process(plugin_dir: str) -> bool:
    """Launches tray_app.py in the user's graphical desktop session."""
    script_path = os.path.join(plugin_dir, "tray", "tray_app.py")
    if not os.path.exists(script_path):
        return False

    # If desktop session is not active (e.g. running in Steam Game Mode),
    # autostart desktop entry will launch the tray companion when switching to Desktop Mode.
    if not is_desktop_session_active():
        return True

    # Check if already running
    try:
        res = subprocess.run(
            ["pgrep", "-f", "zapret.*tray_app.py"], stdout=subprocess.PIPE
        )
        if res.returncode == 0 and res.stdout.strip():
            return True
    except Exception:
        pass

    user_home = get_user_home()
    user_name = os.path.basename(user_home) or "deck"

    uid = 1000
    try:
        import pwd

        uid = pwd.getpwnam(user_name).pw_uid
    except Exception:
        pass

    # Try launching via systemd-run --user first (best for SteamOS session isolation)
    try:
        if os.geteuid() == 0:
            res = subprocess.run(
                [
                    "systemd-run",
                    "--user",
                    "-M",
                    f"{user_name}@",
                    "--unit=zapret-deck-tray",
                    "python3",
                    script_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if res.returncode == 0:
                return True
        else:
            res = subprocess.run(
                [
                    "systemd-run",
                    "--user",
                    "--unit=zapret-deck-tray",
                    "python3",
                    script_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if res.returncode == 0:
                return True
    except Exception:
        pass

    # Fallback to direct subprocess spawn
    display = os.environ.get("DISPLAY", ":0")
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "wayland-0")

    cmd = ["python3", script_path]

    if os.geteuid() == 0:
        cmd = [
            "sudo",
            "-u",
            user_name,
            "env",
            f"DISPLAY={display}",
            f"WAYLAND_DISPLAY={wayland_display}",
            f"XDG_RUNTIME_DIR=/run/user/{uid}",
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
            "python3",
            script_path,
        ]

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception as e:
        print(f"Failed to launch tray process: {e}")
        return False

