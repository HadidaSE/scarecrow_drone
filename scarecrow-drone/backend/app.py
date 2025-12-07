from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from controllers.drone_controller import drone_router
from controllers.flight_controller import flight_router
from controllers.connection_controller import connection_router
from services.drone_connection import DroneConnection
from services.connection_service import ConnectionService

app = FastAPI(title="Scarecrow Drone API")
drone_connection = DroneConnection()
connection_service = ConnectionService()

# Wire up ConnectionService to DroneConnection for SSH data updates
connection_service.set_drone_connection(drone_connection)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(drone_router, prefix="/api/drone", tags=["drone"])
app.include_router(flight_router, prefix="/api/flights", tags=["flights"])
app.include_router(connection_router, prefix="/api/connection", tags=["connection"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.websocket("/ws/drone")
async def websocket_drone(websocket: WebSocket):
    """WebSocket endpoint for drone connection"""
    await drone_connection.connect_drone(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await drone_connection.receive_drone_data(data)
    except WebSocketDisconnect:
        await drone_connection.disconnect_drone()


@app.websocket("/ws/frontend")
async def websocket_frontend(websocket: WebSocket):
    """WebSocket endpoint for frontend to receive real-time updates"""
    await drone_connection.connect_frontend(websocket)
    try:
        while True:
            # Keep connection alive, frontend just listens
            await websocket.receive_text()
    except WebSocketDisconnect:
        drone_connection.disconnect_frontend(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
