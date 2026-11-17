import os
import subprocess
import webbrowser
import ctypes
import psutil
from typing import Dict, Any, List


class AppController:
    """
    App Control Tool module for AIRA.
    Handles launching, switching, closing applications, media keys, and web browsing.
    """

    APP_MAP = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "chrome": "chrome",
        "google chrome": "chrome",
        "edge": "msedge",
        "browser": "msedge",
        "vscode": "code",
        "code": "code",
        "spotify": "spotify",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "powershell.exe",
        "powershell": "powershell.exe",
        "paint": "mspaint.exe",
        "task manager": "taskmgr.exe",
    }

    @staticmethod
    def launch_app(app_name: str) -> Dict[str, Any]:
        """Launch an application by common name or executable path."""
        try:
            name_clean = app_name.strip().lower()
            cmd = AppController.APP_MAP.get(name_clean, name_clean)

            # Spawn application detached so it doesn't block the backend
            subprocess.Popen(cmd, shell=True)
            return {"status": "success", "message": f"Successfully launched {app_name}."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch {app_name}: {str(e)}"}

    @staticmethod
    def close_app(app_name: str) -> Dict[str, Any]:
        """Terminate processes matching app_name."""
        try:
            target = app_name.strip().lower().replace(".exe", "")
            killed = 0
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pname = proc.info["name"].lower()
                    if target in pname:
                        proc.terminate()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if killed > 0:
                return {"status": "success", "message": f"Closed {killed} instance(s) of {app_name}."}
            else:
                return {"status": "warning", "message": f"No running application matching '{app_name}' was found."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to close {app_name}: {str(e)}"}

    @staticmethod
    def open_url(url: str) -> Dict[str, Any]:
        """Open a website or link in the default browser."""
        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            webbrowser.open(url)
            return {"status": "success", "message": f"Opened {url} in browser."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open URL {url}: {str(e)}"}

    @staticmethod
    def media_control(action: str) -> Dict[str, Any]:
        """
        Control media playback.
        action: 'play_pause', 'next', 'previous', 'stop'
        """
        try:
            VK_MEDIA_NEXT_TRACK = 0xB0
            VK_MEDIA_PREV_TRACK = 0xB1
            VK_MEDIA_STOP = 0xB2
            VK_MEDIA_PLAY_PAUSE = 0xB3
            KEYEVENTF_KEYUP = 0x0002

            def press(vk):
                ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

            act = action.lower()
            if act in ["play", "pause", "play_pause", "toggle"]:
                press(VK_MEDIA_PLAY_PAUSE)
                return {"status": "success", "message": "Media Play/Pause toggled."}
            elif act in ["next", "skip"]:
                press(VK_MEDIA_NEXT_TRACK)
                return {"status": "success", "message": "Skipped to next track."}
            elif act in ["prev", "previous", "back"]:
                press(VK_MEDIA_PREV_TRACK)
                return {"status": "success", "message": "Skipped to previous track."}
            elif act == "stop":
                press(VK_MEDIA_STOP)
                return {"status": "success", "message": "Media playback stopped."}
            else:
                return {"status": "error", "message": f"Unknown media action: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"Media control failed: {str(e)}"}

    @staticmethod
    def list_running_apps() -> Dict[str, Any]:
        """List major running desktop applications."""
        try:
            apps = set()
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"]
                    if name.endswith(".exe"):
                        apps.add(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return {"status": "success", "apps": sorted(list(apps))[:30]}
        except Exception as e:
            return {"status": "error", "message": f"Failed to list applications: {str(e)}"}


app_controller = AppController()

