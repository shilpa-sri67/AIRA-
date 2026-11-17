import os
import sys
import subprocess
import platform
import ctypes
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pyperclip
except ImportError:
    pyperclip = None


class OSController:
    """
    OS Control Tool module for AIRA.
    Handles system-level commands: Volume, Brightness, Power, System Stats, Clipboard, and File explorer.
    """

    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Get CPU, Memory, Disk, and Battery usage statistics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            
            battery = psutil.sensors_battery()
            battery_info = None
            if battery:
                power_unlimited = getattr(psutil, "POWER_TIME_UNLIMITED", -1)
                battery_info = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "seconds_left": battery.secsleft if battery.secsleft != power_unlimited else "unlimited",
                }

            return {
                "status": "success",
                "os": f"{platform.system()} {platform.release()}",
                "cpu_percent": f"{cpu_percent}%",
                "memory_used": f"{round(memory.used / (1024**3), 2)} GB / {round(memory.total / (1024**3), 2)} GB ({memory.percent}%)",
                "disk_free": f"{round(disk.free / (1024**3), 2)} GB free of {round(disk.total / (1024**3), 2)} GB",
                "battery": battery_info,
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to get system stats: {str(e)}"}

    @staticmethod
    def adjust_volume(action: str, value: Optional[int] = None) -> Dict[str, Any]:
        """
        Adjust volume.
        action: 'up', 'down', 'mute', 'unmute', or 'set'
        value: optional integer (0 to 100) for 'set' or steps for 'up'/'down'
        """
        if platform.system() != "Windows":
            return {"status": "error", "message": "OS volume control is currently implemented for Windows."}

        try:
            # Using Windows key events for volume control
            VK_VOLUME_MUTE = 0xAD
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF
            KEYEVENTF_KEYUP = 0x0002

            def press_key(vk_code):
                ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

            action = action.lower()
            if action == "mute" or action == "unmute":
                press_key(VK_VOLUME_MUTE)
                return {"status": "success", "message": f"Volume toggle mute performed."}
            elif action == "up":
                steps = int(value) if value else 5
                for _ in range(steps):
                    press_key(VK_VOLUME_UP)
                return {"status": "success", "message": f"Volume increased by {steps * 2}%."}
            elif action == "down":
                steps = int(value) if value else 5
                for _ in range(steps):
                    press_key(VK_VOLUME_DOWN)
                return {"status": "success", "message": f"Volume decreased by {steps * 2}%."}
            elif action == "set":
                # PowerShell volume set command
                target = max(0, min(100, int(value if value is not None else 50)))
                ps_script = f"""
                $obj = New-Object -ComObject WScript.Shell
                1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
                1..{target // 2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
                """
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
                return {"status": "success", "message": f"Volume set approximately to {target}%."}
            else:
                return {"status": "error", "message": f"Unknown volume action: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to adjust volume: {str(e)}"}

    @staticmethod
    def adjust_brightness(level: int) -> Dict[str, Any]:
        """Set screen brightness (0-100) via WMI on Windows."""
        try:
            level = max(0, min(100, int(level)))
            ps_cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
            res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {"status": "success", "message": f"Brightness set to {level}%."}
            else:
                return {"status": "error", "message": res.stderr.strip() or "Brightness change not supported on this display."}
        except Exception as e:
            return {"status": "error", "message": f"Brightness adjustment failed: {str(e)}"}

    @staticmethod
    def take_screenshot(filename: Optional[str] = None) -> Dict[str, Any]:
        """Capture desktop screenshot and save to disk."""
        try:
            if pyautogui is None:
                return {"status": "error", "message": "pyautogui is not installed."}

            save_dir = os.path.join(os.getcwd(), "cache", "screenshots")
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = filename or f"screenshot_{timestamp}.png"
            full_path = os.path.join(save_dir, fname)

            screenshot = pyautogui.screenshot()
            screenshot.save(full_path)

            return {
                "status": "success",
                "message": f"Screenshot saved successfully.",
                "file_path": full_path,
            }
        except Exception as e:
            return {"status": "error", "message": f"Screenshot failed: {str(e)}"}

    @staticmethod
    def lock_screen() -> Dict[str, Any]:
        """Lock the Windows workstation."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return {"status": "success", "message": "Workstation locked successfully."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to lock screen: {str(e)}"}

    @staticmethod
    def manage_clipboard(action: str, text: Optional[str] = None) -> Dict[str, Any]:
        """
        Clipboard helper.
        action: 'copy' or 'paste'/'get'
        """
        try:
            if pyperclip is None:
                return {"status": "error", "message": "pyperclip is not installed."}

            if action.lower() == "copy":
                pyperclip.copy(text or "")
                return {"status": "success", "message": "Text copied to clipboard."}
            elif action.lower() in ["get", "paste", "read"]:
                content = pyperclip.paste()
                return {"status": "success", "content": content}
            else:
                return {"status": "error", "message": f"Unknown clipboard action: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"Clipboard operation failed: {str(e)}"}

    @staticmethod
    def open_folder(path: str) -> Dict[str, Any]:
        """Open a directory or file in Windows Explorer."""
        try:
            target = os.path.expanduser(path)
            if not os.path.exists(target):
                return {"status": "error", "message": f"Path not found: {path}"}
            os.startfile(target)
            return {"status": "success", "message": f"Opened {path}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open path: {str(e)}"}


os_controller = OSController()
