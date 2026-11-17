import logging
from typing import Dict, Any, List, Tuple
from backend.tools.os_control import os_controller
from backend.tools.app_control import app_controller
from backend.tools.iot_control import iot_controller

logger = logging.getLogger("aira.tool_router")


class ToolRouter:
    """
    TOOL ROUTER + VERIFICATION ENGINE
    Routes decisions and planned function calls from the Python Agent Core (Gemini 3.8 Flash)
    to the respective controller (OS Control, App Control, IoT Control).
    Performs verification on inputs and verifies post-execution status.
    """

    def __init__(self):
        self.os = os_controller
        self.app = app_controller
        self.iot = iot_controller

    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """
        Returns Gemini-compatible tool schemas for function calling.
        """
        return [
            # OS Control Tools
            {
                "name": "get_system_stats",
                "description": "Get current OS stats: CPU usage, memory, disk space, and battery status.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {},
                },
            },
            {
                "name": "adjust_volume",
                "description": "Control system volume: increase, decrease, mute, or set a specific level.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Action to perform: 'up', 'down', 'mute', 'unmute', or 'set'.",
                        },
                        "value": {
                            "type": "INTEGER",
                            "description": "Target volume percentage (0-100) if action is 'set', or number of steps for up/down.",
                        },
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "adjust_brightness",
                "description": "Change display brightness percentage (0-100).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "level": {
                            "type": "INTEGER",
                            "description": "Brightness percentage from 0 to 100.",
                        }
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "take_screenshot",
                "description": "Capture the current desktop screen and save as an image.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {
                            "type": "STRING",
                            "description": "Optional custom filename for the screenshot.",
                        }
                    },
                },
            },
            {
                "name": "lock_screen",
                "description": "Locks the current workstation/computer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {},
                },
            },
            {
                "name": "manage_clipboard",
                "description": "Read from or copy text to the system clipboard.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "'copy' to set clipboard text, or 'get' to read current clipboard.",
                        },
                        "text": {
                            "type": "STRING",
                            "description": "Text to copy (only required if action is 'copy').",
                        },
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "open_folder",
                "description": "Open a folder or file path in File Explorer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {
                            "type": "STRING",
                            "description": "Path to folder or file (e.g. 'Downloads', 'C:/Users/LENOVO/Desktop', '.').",
                        }
                    },
                    "required": ["path"],
                },
            },

            # App Control Tools
            {
                "name": "launch_app",
                "description": "Launch a desktop app or program (e.g., chrome, notepad, spotify, calculator, vscode, terminal).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app_name": {
                            "type": "STRING",
                            "description": "Name or executable of the program to open.",
                        }
                    },
                    "required": ["app_name"],
                },
            },
            {
                "name": "close_app",
                "description": "Terminate or close a running application by name.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app_name": {
                            "type": "STRING",
                            "description": "Name of the application or process to close.",
                        }
                    },
                    "required": ["app_name"],
                },
            },
            {
                "name": "open_url",
                "description": "Open a web URL in the default internet browser.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {
                            "type": "STRING",
                            "description": "The URL or website address to visit.",
                        }
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "media_control",
                "description": "Control playback of music/video: play/pause, next track, previous track, stop.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "'play_pause', 'next', 'previous', or 'stop'.",
                        }
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "list_running_apps",
                "description": "List currently running desktop applications.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {},
                },
            },

            # IoT Control Tools
            {
                "name": "control_light",
                "description": "Control smart lights: turn on/off, change brightness, or set light color.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "room": {
                            "type": "STRING",
                            "description": "Room or light identifier ('living_room', 'bedroom', 'studio', 'kitchen', 'all').",
                        },
                        "state": {
                            "type": "STRING",
                            "description": "'on' or 'off'.",
                        },
                        "brightness": {
                            "type": "INTEGER",
                            "description": "Brightness percentage from 0 to 100.",
                        },
                        "color": {
                            "type": "STRING",
                            "description": "Color name or temperature (e.g. 'warm white', 'blue', 'cyberpunk pink', 'daylight').",
                        },
                    },
                    "required": ["room"],
                },
            },
            {
                "name": "control_plug",
                "description": "Turn smart plug or power outlet on or off.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "plug_name": {
                            "type": "STRING",
                            "description": "Plug name: 'desk_charger', 'coffee_maker', or 'fan'.",
                        },
                        "state": {
                            "type": "STRING",
                            "description": "'on' or 'off'.",
                        },
                    },
                    "required": ["plug_name", "state"],
                },
            },
            {
                "name": "control_thermostat",
                "description": "Set temperature and mode on the smart thermostat / air conditioner.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "target_temp": {
                            "type": "INTEGER",
                            "description": "Target temperature in Celsius (16-30).",
                        },
                        "mode": {
                            "type": "STRING",
                            "description": "Mode: 'cool', 'heat', 'eco', 'off', or 'fan'.",
                        },
                    },
                },
            },
            {
                "name": "activate_scene",
                "description": "Activate a predefined smart home scene preset: 'movie_night', 'focus_mode', 'good_morning', or 'sleep'.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "scene_name": {
                            "type": "STRING",
                            "description": "Scene name to activate.",
                        }
                    },
                    "required": ["scene_name"],
                },
            },
            {
                "name": "get_iot_status",
                "description": "Query the state of all smart home IoT devices (lights, plugs, thermostat, curtains).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {},
                },
            },
        ]

    def _verify_arguments(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """
        PRE-EXECUTION VERIFICATION STEP:
        Ensures arguments are valid, safe, and within allowable bounds.
        """
        if tool_name == "adjust_brightness":
            lvl = args.get("level")
            if lvl is not None and not (0 <= int(lvl) <= 100):
                return False, f"Verification failed: brightness level must be between 0 and 100, got {lvl}."

        elif tool_name == "adjust_volume":
            val = args.get("value")
            if val is not None and not (0 <= int(val) <= 100):
                return False, f"Verification failed: volume value must be between 0 and 100, got {val}."

        elif tool_name == "control_thermostat":
            temp = args.get("target_temp")
            if temp is not None and not (16 <= int(temp) <= 32):
                return False, f"Verification failed: temperature must be between 16°C and 32°C, got {temp}."

        return True, "Pre-execution parameters verified."

    def execute_and_verify(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ROUTING + EXECUTION + POST-EXECUTION VERIFICATION:
        1. Verifies input constraints
        2. Routes to OS, App, or IoT
        3. Executes the action
        4. Verifies post-execution status & prepares verified return payload
        """
        logger.info(f"Routing tool call: {tool_name} with args: {args}")

        # 1. Pre-execution verification
        is_valid, verify_msg = self._verify_arguments(tool_name, args)
        if not is_valid:
            return {
                "verified": False,
                "domain": "Verification",
                "status": "error",
                "message": verify_msg,
            }

        # 2. Routing
        try:
            domain = "Unknown"
            result: Dict[str, Any] = {}

            # OS CONTROL ROUTING
            if tool_name == "get_system_stats":
                domain = "OS Control"
                result = self.os.get_system_stats()
            elif tool_name == "adjust_volume":
                domain = "OS Control"
                result = self.os.adjust_volume(args.get("action", ""), args.get("value"))
            elif tool_name == "adjust_brightness":
                domain = "OS Control"
                result = self.os.adjust_brightness(args.get("level", 50))
            elif tool_name == "take_screenshot":
                domain = "OS Control"
                result = self.os.take_screenshot(args.get("filename"))
            elif tool_name == "lock_screen":
                domain = "OS Control"
                result = self.os.lock_screen()
            elif tool_name == "manage_clipboard":
                domain = "OS Control"
                result = self.os.manage_clipboard(args.get("action", ""), args.get("text"))
            elif tool_name == "open_folder":
                domain = "OS Control"
                result = self.os.open_folder(args.get("path", ""))

            # APP CONTROL ROUTING
            elif tool_name == "launch_app":
                domain = "App Control"
                result = self.app.launch_app(args.get("app_name", ""))
            elif tool_name == "close_app":
                domain = "App Control"
                result = self.app.close_app(args.get("app_name", ""))
            elif tool_name == "open_url":
                domain = "App Control"
                result = self.app.open_url(args.get("url", ""))
            elif tool_name == "media_control":
                domain = "App Control"
                result = self.app.media_control(args.get("action", ""))
            elif tool_name == "list_running_apps":
                domain = "App Control"
                result = self.app.list_running_apps()

            # IOT CONTROL ROUTING
            elif tool_name == "control_light":
                domain = "IoT Control"
                result = self.iot.control_light(
                    room=args.get("room", "all"),
                    state=args.get("state"),
                    brightness=args.get("brightness"),
                    color=args.get("color"),
                )
            elif tool_name == "control_plug":
                domain = "IoT Control"
                result = self.iot.control_plug(
                    plug_name=args.get("plug_name", ""),
                    state=args.get("state", "on"),
                )
            elif tool_name == "control_thermostat":
                domain = "IoT Control"
                result = self.iot.control_thermostat(
                    target_temp=args.get("target_temp"),
                    mode=args.get("mode"),
                )
            elif tool_name == "activate_scene":
                domain = "IoT Control"
                result = self.iot.activate_scene(args.get("scene_name", ""))
            elif tool_name == "get_iot_status":
                domain = "IoT Control"
                result = self.iot.get_status()
            else:
                return {
                    "verified": False,
                    "domain": "Router",
                    "status": "error",
                    "message": f"No registered handler for tool '{tool_name}'.",
                }

            # 3. Post-execution verification
            is_success = result.get("status") in ["success", "warning"]
            return {
                "verified": is_success,
                "tool": tool_name,
                "domain": domain,
                "status": result.get("status", "success"),
                "result": result,
                "verification_notes": "Action executed and verified." if is_success else f"Action execution reported issue: {result.get('message')}",
            }

        except Exception as e:
            logger.error(f"Execution error on {tool_name}: {e}", exc_info=True)
            return {
                "verified": False,
                "tool": tool_name,
                "domain": "Error",
                "status": "error",
                "message": f"Execution failed unexpectedly: {str(e)}",
            }


tool_router = ToolRouter()

