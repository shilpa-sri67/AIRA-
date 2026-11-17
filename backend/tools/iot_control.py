import json
import os
from typing import Dict, Any, Optional


class IoTController:
    """
    IoT Control Tool module for AIRA.
    Controls smart home devices: Lights, Plugs, Thermostats, Scenes, and Home Assistant bridging.
    Maintains an in-memory & file-persisted state of the smart environment.
    """

    STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "iot_state.json")

    def __init__(self):
        self.devices: Dict[str, Any] = {
            "lights": {
                "living_room": {"name": "Living Room Light", "state": "off", "brightness": 80, "color": "warm white"},
                "bedroom": {"name": "Bedroom Light", "state": "off", "brightness": 60, "color": "soft amber"},
                "studio": {"name": "Studio & Desk Light", "state": "on", "brightness": 100, "color": "daylight cyan"},
                "kitchen": {"name": "Kitchen Ceiling Light", "state": "off", "brightness": 90, "color": "white"},
            },
            "plugs": {
                "desk_charger": {"name": "Desk Charger Plug", "state": "on", "current_watts": 45},
                "coffee_maker": {"name": "Smart Coffee Maker", "state": "off", "current_watts": 0},
                "fan": {"name": "Tower Fan", "state": "off", "current_watts": 0},
            },
            "thermostat": {
                "current_temp": 24,
                "target_temp": 22,
                "mode": "cool",  # cool, heat, eco, off
                "fan_speed": "auto",
            },
            "curtains": {
                "studio_blinds": {"name": "Studio Blinds", "position": 100},  # 0: closed, 100: open
            },
        }
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(self.STATE_FILE):
                with open(self.STATE_FILE, "r") as f:
                    saved = json.load(f)
                    self.devices.update(saved)
        except Exception:
            pass

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            with open(self.STATE_FILE, "w") as f:
                json.dump(self.devices, f, indent=2)
        except Exception:
            pass

    def control_light(
        self,
        room: str,
        state: Optional[str] = None,
        brightness: Optional[int] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Turn smart light on/off, adjust brightness (0-100), or change color.
        room: 'living_room', 'bedroom', 'studio', 'kitchen', or 'all'
        state: 'on' or 'off'
        """
        target_room = room.strip().lower().replace(" ", "_")
        targets = []

        if target_room in ["all", "everything", "everywhere"]:
            targets = list(self.devices["lights"].keys())
        elif target_room in self.devices["lights"]:
            targets = [target_room]
        else:
            # Fuzzy match
            for k in self.devices["lights"]:
                if target_room in k:
                    targets.append(k)

        if not targets:
            return {"status": "error", "message": f"Light room '{room}' not found. Available: {list(self.devices['lights'].keys())}"}

        changes = []
        for t in targets:
            light = self.devices["lights"][t]
            if state:
                light["state"] = state.lower()
            if brightness is not None:
                light["brightness"] = max(0, min(100, int(brightness)))
                if light["brightness"] > 0:
                    light["state"] = "on"
            if color:
                light["color"] = color
                light["state"] = "on"
            changes.append(f"{light['name']} is now {light['state']} (Brightness: {light['brightness']}%, Color: {light['color']})")

        self._save_state()
        return {"status": "success", "message": " | ".join(changes), "devices": self.devices["lights"]}

    def control_plug(self, plug_name: str, state: str) -> Dict[str, Any]:
        """
        Turn smart plug on or off.
        plug_name: 'desk_charger', 'coffee_maker', 'fan', etc.
        state: 'on' or 'off'
        """
        target = plug_name.strip().lower().replace(" ", "_")
        matched_key = None
        for k in self.devices["plugs"]:
            if target in k:
                matched_key = k
                break

        if not matched_key:
            return {"status": "error", "message": f"Plug '{plug_name}' not found. Available: {list(self.devices['plugs'].keys())}"}

        plug = self.devices["plugs"][matched_key]
        plug["state"] = state.lower()
        if plug["state"] == "on":
            plug["current_watts"] = 65 if "charger" in matched_key else (800 if "coffee" in matched_key else 35)
        else:
            plug["current_watts"] = 0

        self._save_state()
        return {"status": "success", "message": f"{plug['name']} turned {plug['state']}.", "device": plug}

    def control_thermostat(
        self,
        target_temp: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Control AC / Thermostat target temperature and mode (cool, heat, eco, off).
        """
        t = self.devices["thermostat"]
        if target_temp is not None:
            t["target_temp"] = max(16, min(30, int(target_temp)))
        if mode:
            mode_clean = mode.lower()
            if mode_clean in ["cool", "heat", "eco", "off", "fan"]:
                t["mode"] = mode_clean

        self._save_state()
        return {
            "status": "success",
            "message": f"Thermostat set to {t['target_temp']}°C in {t['mode']} mode (Current: {t['current_temp']}°C).",
            "thermostat": t,
        }

    def activate_scene(self, scene_name: str) -> Dict[str, Any]:
        """
        Activate smart scene preset:
        - 'movie_night' / 'cinema'
        - 'focus_mode' / 'work'
        - 'good_morning'
        - 'sleep' / 'night'
        """
        scene = scene_name.strip().lower().replace(" ", "_")
        if scene in ["movie_night", "cinema", "movie"]:
            self.devices["lights"]["living_room"] = {"name": "Living Room Light", "state": "on", "brightness": 15, "color": "deep indigo"}
            self.devices["lights"]["studio"]["state"] = "off"
            self.devices["thermostat"]["target_temp"] = 22
            msg = "Cinema Scene activated: Living room dimmed to 15% indigo, AC set to 22°C."
        elif scene in ["focus_mode", "work", "focus"]:
            self.devices["lights"]["studio"] = {"name": "Studio & Desk Light", "state": "on", "brightness": 100, "color": "daylight 5000K"}
            self.devices["plugs"]["desk_charger"]["state"] = "on"
            msg = "Focus Mode activated: Desk light set to 100% daylight, workstation energized."
        elif scene in ["good_morning", "morning"]:
            for k in self.devices["lights"]:
                self.devices["lights"][k]["state"] = "on"
                self.devices["lights"][k]["brightness"] = 70
                self.devices["lights"][k]["color"] = "natural sunrise"
            self.devices["plugs"]["coffee_maker"]["state"] = "on"
            self.devices["curtains"]["studio_blinds"]["position"] = 100
            msg = "Good Morning scene activated: Sunrise lighting enabled, coffee maker brewing, blinds opened."
        elif scene in ["sleep", "night", "good_night"]:
            for k in self.devices["lights"]:
                self.devices["lights"][k]["state"] = "off"
            self.devices["curtains"]["studio_blinds"]["position"] = 0
            self.devices["thermostat"]["target_temp"] = 21
            msg = "Night Scene activated: All lights turned off, blinds closed, temperature adjusted to 21°C."
        else:
            return {"status": "error", "message": f"Unknown scene: '{scene_name}'. Valid scenes: 'movie_night', 'focus_mode', 'good_morning', 'sleep'."}

        self._save_state()
        return {"status": "success", "scene": scene, "message": msg}

    def get_status(self) -> Dict[str, Any]:
        """Get status of all connected IoT devices."""
        return {"status": "success", "environment": self.devices}


iot_controller = IoTController()

