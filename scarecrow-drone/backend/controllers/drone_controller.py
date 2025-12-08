from fastapi import APIRouter
from services.drone_service import DroneService
from services.connection_service import ConnectionService

drone_router = APIRouter()
drone_service = DroneService()
connection_service = ConnectionService()


@drone_router.get("/status")
def get_status():
    """GET /api/drone/status - Get drone status"""
    result = drone_service.get_status()
    return result


@drone_router.post("/start")
async def start_flight():
    """POST /api/drone/start - Start flight"""
    result = await drone_service.start_flight()
    return result


@drone_router.post("/stop")
async def stop_flight():
    """POST /api/drone/stop - Stop flight (return home)"""
    result = await drone_service.stop_flight()
    return result


@drone_router.post("/return-home")
def return_home():
    """POST /api/drone/return-home - Command drone to return to starting position"""
    result = connection_service.return_home()
    return result


@drone_router.post("/abort")
async def abort_mission():
    """POST /api/drone/abort - Emergency abort, terminate all tasks and land immediately"""
    result = await drone_service.abort_mission()
    return result
