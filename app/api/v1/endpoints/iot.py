from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from backend.tools.iot_control import iot_controller

router = APIRouter()


class LightControlRequest(BaseModel):
    room: str
    state: Optional[str] = None
    brightness: Optional[int] = None
    color: Optional[str] = None


class PlugControlRequest(BaseModel):
    plug_name: str
    state: str


class ThermostatRequest(BaseModel):
    target_temp: Optional[int] = None
    mode: Optional[str] = None


class SceneRequest(BaseModel):
    scene_name: str


@router.get("/devices", tags=["IoT Control"])
def get_all_devices():
    """Get status of all connected IoT smart home devices."""
    return iot_controller.get_status()


@router.post("/light", tags=["IoT Control"])
def control_light_api(req: LightControlRequest):
    """Control smart light."""
    return iot_controller.control_light(
        room=req.room,
        state=req.state,
        brightness=req.brightness,
        color=req.color,
    )


@router.post("/plug", tags=["IoT Control"])
def control_plug_api(req: PlugControlRequest):
    """Control smart plug."""
    return iot_controller.control_plug(
        plug_name=req.plug_name,
        state=req.state,
    )


@router.post("/thermostat", tags=["IoT Control"])
def control_thermostat_api(req: ThermostatRequest):
    """Control smart thermostat / AC."""
    return iot_controller.control_thermostat(
        target_temp=req.target_temp,
        mode=req.mode,
    )


@router.post("/scene", tags=["IoT Control"])
def activate_scene_api(req: SceneRequest):
    """Activate smart home scene."""
    return iot_controller.activate_scene(scene_name=req.scene_name)

