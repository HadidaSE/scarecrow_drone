from fastapi import APIRouter, HTTPException
from services.flight_service import FlightService

flight_router = APIRouter()
flight_service = FlightService()


@flight_router.get("")
def get_flight_history():
    """GET /api/flights - Get flight history"""
    result = flight_service.get_flight_history()
    return result


@flight_router.get("/{flight_id}/summary")
def get_flight_summary(flight_id: str):
    """GET /api/flights/:flightId/summary - Get flight summary with stats"""
    result = flight_service.get_flight_summary(flight_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return result


@flight_router.get("/{flight_id}/images")
def get_flight_images(flight_id: str):
    """GET /api/flights/:flightId/images - Get detection image paths for a flight"""
    images = flight_service.get_detection_images(flight_id)
    return {"images": images}


@flight_router.get("/{flight_id}/recording")
def get_flight_recording(flight_id: str):
    """GET /api/flights/:flightId/recording - Get video recording path for a flight"""
    recording = flight_service.get_flight_recording(flight_id)
    return {"recording": recording}


@flight_router.get("/{flight_id}")
def get_flight(flight_id: str):
    """GET /api/flights/:flightId - Get single flight details"""
    result = flight_service.get_flight(flight_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return result
