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


@flight_router.get("/{flight_id}")
def get_flight(flight_id: str):
    """GET /api/flights/:flightId - Get single flight details"""
    result = flight_service.get_flight(flight_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return result
