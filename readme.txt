===============================================================================
                    SCARECROW DRONE - BIRD DETECTION SYSTEM
                                    README
===============================================================================

Version : 1.0 (Secondary Alpha Implementation)
Date    : January 2026
Design  : See ADD_Scarecrow_Drone_Professional.docx / .txt for the full
          Application Design Document (use cases, diagrams, OCL specs).


-------------------------------------------------------------------------------
1. OVERVIEW
-------------------------------------------------------------------------------

Scarecrow Drone is an autonomous pigeon-deterrence system. A drone patrols a
pre-mapped area, streams live video to a ground station, and a YOLOv8 model
detects birds (pigeons) in the video. When birds are detected, the drone
pursues them and applies counter-measures (deterrent sound and/or aggressive
movement patterns) until they disperse, then returns to its patrol route.

Every flight is recorded: video, annotated detection images, telemetry
(battery, distance, detection count) and chase events are stored and can be
reviewed later from a web dashboard.


-------------------------------------------------------------------------------
2. MAIN FEATURES
-------------------------------------------------------------------------------

  * Area mapping      - Map the target area and define patrol boundaries.
  * Detection flights - Start / stop / abort patrol missions from the browser.
  * Live video        - Real-time camera feed from the drone (RTP/UDP).
  * Bird detection    - YOLOv8 model (best_v4.pt) with a configurable
                        confidence threshold; annotated frames are saved.
  * Chase & deter     - Pursuit of detected birds plus sound / movement /
                        combined counter-measures; outcome is logged
                        (dispersed / lost / aborted).
  * Telemetry         - Battery, distance and detection count, streamed live
                        over WebSocket.
  * Flight history    - Browse past flights, detection galleries, chase logs
                        and recorded videos.
  * Safety            - Abort mission, return-to-home, low-battery (<20%)
                        return, failsafe on connection loss, graceful
                        shutdown on SIGTERM/SIGINT.


-------------------------------------------------------------------------------
3. SYSTEM ARCHITECTURE
-------------------------------------------------------------------------------

  +-----------------------+   HTTP/REST + WebSocket   +----------------------+
  |  Client (browser)     | ------------------------> |  Ground Station      |
  |  React frontend       |                           |  FastAPI backend     |
  |  port 5173            |                           |  port 5000           |
  +-----------------------+                           |  SQLite, detection,  |
                                                      |  file storage        |
                                                      +----------------------+
                                                          |            ^
                                     MAVLink commands     |            |  RTP/UDP
                                     (arm, mode, wpts)    v            |  JPEG video
                                                      +----------------------+
                                                      |  Drone               |
                                                      |  Pixhawk/ArduPilot + |
                                                      |  companion computer  |
                                                      +----------------------+

Frontend (client)
  React 19 + TypeScript single-page app: Dashboard, Area Mapping, Flight
  History, Detection Gallery, Chase Event Log, Telemetry view.

Backend (ground station)
  Python 3.9 + FastAPI, layered architecture:

      controllers  -->  services  -->  database (repositories)  -->  dto

  - controllers/ : REST endpoints (area maps, flights, detection,
                   telemetry, chase events, drone, connection)
  - services/    : business logic (DroneService, FlightService,
                   DetectionService, RecordingService, AreaMapService,
                   TelemetryService, ChaseEventService, ConnectionService)
  - database/    : repositories with all SQL (repository pattern)
  - dto/         : data transfer objects shared by all layers

Detection module
  FFmpeg (stream decode/encode) + YOLOv8 (best_v4.pt) + OpenCV
  (frame processing and bounding-box annotation).

Drone (airborne unit)
  - Flight controller : Pixhawk running ArduPilot (MAVLink)
  - Companion computer: Raspberry Pi / Intel NUC (GStreamer encoder, camera,
                        WiFi / telemetry radio)
  - Hardware          : 640x480 camera, 4/6 motors, 4S LiPo battery,
                        speaker/buzzer for the sound deterrent

Communication
  Protocol          Direction                Port         Purpose
  ---------------   ----------------------   ----------   -------------------
  RTP/UDP (JPEG)    Drone -> Ground station  5000         Live video
  MAVLink           Ground station -> Drone  Serial/WiFi  Flight commands
  MAVLink           Drone -> Ground station  Serial/WiFi  Telemetry
  HTTP/REST + WS    Frontend -> Backend      5000         Web API


-------------------------------------------------------------------------------
4. PROJECT STRUCTURE
-------------------------------------------------------------------------------

scarecrow_drone/
|-- scarecrow-drone/              Main application
|   |-- backend/
|   |   |-- app.py                FastAPI entry point
|   |   |-- controllers/          API route handlers
|   |   |-- services/             Business logic layer
|   |   |-- database/             Data access layer (repositories)
|   |   |-- dto/                  Data transfer objects
|   |   `-- models/               Entity models
|   |-- database/
|   |   |-- database.py           Schema initialization
|   |   `-- scarecrow.db          SQLite database file
|   `-- frontend/
|       |-- public/               Static assets
|       |-- src/
|       |   |-- pages/            Page components
|       |   |-- components/       Reusable UI components
|       |   |-- services/         API client
|       |   |-- types/            TypeScript definitions
|       |   `-- hooks/            Custom React hooks
|       `-- package.json
|-- live_detection/               Detection module
|   |-- pigeon_detector.py        PigeonDetector class
|   |-- best_v4.pt                Trained YOLOv8 model
|   `-- recordings/               Detection video recordings
|-- pigeon-detection/             ML training module
|   |-- src/                      Training scripts
|   |-- data/                     Datasets (train / valid / test)
|   |-- models/                   Saved model weights
|   `-- runs/                     Training run outputs
|-- drone_scripts/                Drone control scripts
|-- tests/
|   |-- backend/unit/             Unit tests
|   |-- backend/integration/      Integration tests
|   |-- detection/                Detection tests
|   `-- e2e/                      End-to-end tests
|-- recordings/                   Flight video recordings
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md


-------------------------------------------------------------------------------
5. REQUIREMENTS
-------------------------------------------------------------------------------

Ground station
  - Python 3.9+
  - Node.js + npm (for the React frontend)
  - FFmpeg and GStreamer 1.0 installed and on PATH
  - Python packages from requirements.txt (FastAPI, Ultralytics YOLOv8,
    OpenCV, MAVLink library, pytest, ...)
  - Docker / Docker Compose (optional, for containerized deployment)

Drone
  - Pixhawk flight controller with ArduPilot firmware
  - Companion computer with camera and GStreamer
  - WiFi link (or SiK telemetry radio) to the ground station


-------------------------------------------------------------------------------
6. GETTING STARTED
-------------------------------------------------------------------------------

Option A - Docker
    docker-compose up --build

Option B - Run locally
    1. Backend
         pip install -r requirements.txt
         cd scarecrow-drone/backend
         python app.py                  (API on http://localhost:5000)

    2. Frontend
         cd scarecrow-drone/frontend
         npm install
         npm run dev                    (UI on http://localhost:5173)

    3. Open http://localhost:5173 in a browser.

Running without hardware
    Set the MOCK_MODE flag to simulate the drone, video stream and
    connection. This is also what the test suite uses.

Note: the exact commands above follow the standard layout described in the
ADD; adjust them if your local scripts differ.


-------------------------------------------------------------------------------
7. TYPICAL WORKFLOW
-------------------------------------------------------------------------------

  1. Connect   - Dashboard -> Connect (WiFi + SSH to the drone, start video).
  2. Map area  - Area Mapping -> "Start Mapping". Review and confirm the
                 boundaries (minimum 3 coordinate points). Map becomes
                 "active".
  3. Fly       - Dashboard -> select area map -> "Start Detection Flight".
                 The drone patrols, records video and runs detection.
  4. Deter     - On detection the system automatically chases the birds and
                 applies counter-measures, then resumes patrol.
  5. Finish    - "Stop Flight" (status: completed) or "Abort Mission"
                 (status: aborted, drone returns home).
  6. Review    - Flight History -> pick a flight to see detection images,
                 chase events, telemetry and the recorded video.


-------------------------------------------------------------------------------
8. DATA MODEL (SQLite)
-------------------------------------------------------------------------------

  area_maps         1 --- *  flights
  flights           1 --- *  detection_images
  flights           1 --- 1  telemetry
  flights           1 --- *  chase_events
  detection_images  1 --- 0..1 chase_events  (triggering detection)

  Table             Key columns
  ---------------   ---------------------------------------------------------
  area_maps         id, name, boundaries (JSON), area_size (m^2),
                    status (active | draft), created_at, updated_at
  flights           id, area_map_id, start_time, end_time, video_path,
                    status (in_progress | completed | failed | aborted)
  detection_images  id, flight_id, image_path, timestamp
  telemetry         flight_id (PK/FK), battery_level (0-100), distance (m),
                    detections
  chase_events      id, flight_id, detection_image_id, start_time, end_time,
                    counter_measure_type (sound | movement | combined),
                    outcome (dispersed | lost | aborted)


-------------------------------------------------------------------------------
9. API REFERENCE (SUMMARY)
-------------------------------------------------------------------------------

Connection
  GET    /api/connection/wifi             WiFi connection status
  POST   /api/connection/ssh              Connect SSH to drone
  DELETE /api/connection/ssh              Disconnect SSH
  GET    /api/connection/status           Full connection status
  POST   /api/connection/video/start      Start video stream
  POST   /api/connection/video/stop       Stop video stream

Drone control
  GET    /api/drone/status                Drone operational status
  POST   /api/drone/start                 Start mission  { areaMapId? }
  POST   /api/drone/stop                  Stop mission gracefully
  POST   /api/drone/abort                 Emergency abort
  POST   /api/drone/return-home           Return to home
  GET    /api/drone/telemetry             Current telemetry
  WS     /api/drone/telemetry/stream      Real-time telemetry stream

Flights
  GET    /api/flights                     All flights
  GET    /api/flights/{id}                Flight details
  GET    /api/flights/{id}/summary        Duration, avg speed, detections
  GET    /api/flights/{id}/images         Detection images
  GET    /api/flights/{id}/recording      Video recording path
  GET    /api/flights/{id}/telemetry      Telemetry history
  GET    /api/flights/{id}/chases         Chase events
  DELETE /api/flights/{id}                Delete flight

Area maps
  GET    /api/areas                       All area maps
  GET    /api/areas/{id}                  Area map details
  POST   /api/areas                       Create  { name, boundaries, homePoint }
  PUT    /api/areas/{id}                  Update
  DELETE /api/areas/{id}                  Delete
  GET    /api/areas/{id}/flights          Flights for an area
  POST   /api/areas/mapping/start         Start mapping flight  { name }
  GET    /api/areas/mapping/status        Mapping progress

Detection / chases
  GET    /api/detection/status            Detection service status
  GET    /api/detection/config            Confidence threshold, model path
  PUT    /api/detection/config            Update confidence threshold
  GET    /api/chases/{id}                 Chase event details


-------------------------------------------------------------------------------
10. TESTING
-------------------------------------------------------------------------------

  Level         Tools                                 Location
  -----------   -----------------------------------   ------------------------
  Unit          pytest, pytest-asyncio                tests/backend/unit
                Jest + React Testing Library          (frontend)
  Integration   pytest + FastAPI TestClient           tests/backend/integration
  Detection     pytest                                tests/detection
  End-to-end    Playwright                            tests/e2e

  - Tests use an in-memory SQLite database.
  - Hardware is simulated with the MOCK_MODE flag.
  - Unit tests check the OCL invariants, pre- and post-conditions defined in
    the ADD (e.g. battery 0-100, end_time >= start_time, valid status and
    counter-measure values, area maps with at least 3 boundary points).

  Run the backend tests:
      pytest tests/


-------------------------------------------------------------------------------
11. DOCUMENTATION
-------------------------------------------------------------------------------

  ADD_Scarecrow_Drone_Professional.docx / .txt - full design document:
    1. Use cases (UC1-UC8)          5. Object-oriented model + OCL
    2. System architecture          6. User interface drafts
    3. Data model / ERD             7. Test plan
    4. Sequence diagrams, events,   A. API endpoints
       state machines               B. File structure

===============================================================================
