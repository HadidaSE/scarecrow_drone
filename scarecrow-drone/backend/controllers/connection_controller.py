from fastapi import APIRouter
from services.connection_service import ConnectionService

connection_router = APIRouter()
connection_service = ConnectionService()


@connection_router.get("/wifi")
def check_wifi():
    """GET /api/connection/wifi - Check WiFi connection to drone"""
    result = connection_service.check_wifi_connection()
    return result


@connection_router.post("/ssh")
async def connect_ssh():
    """POST /api/connection/ssh - Connect to drone via SSH"""
    result = await connection_service.connect_ssh()
    return result


@connection_router.delete("/ssh")
def disconnect_ssh():
    """DELETE /api/connection/ssh - Disconnect SSH"""
    result = connection_service.disconnect_ssh()
    return result


@connection_router.get("/status")
def get_connection_status():
    """GET /api/connection/status - Get full connection status"""
    result = connection_service.get_connection_status()
    return result
