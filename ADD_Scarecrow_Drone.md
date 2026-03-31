# Application Design Document (ADD)
# Scarecrow Drone - Bird Detection System

**Version:** 1.0
**Date:** January 2026
**Project:** Scarecrow Drone - Secondary Alpha Implementation

---

## Table of Contents

1. [Use Cases](#1-use-cases)
2. [System Architecture](#2-system-architecture)
3. [Data Model](#3-data-model)
4. [Behavioral Analysis](#4-behavioral-analysis)
5. [Object-Oriented Model](#5-object-oriented-model)
6. [User Interface Draft](#6-user-interface-draft)
7. [Testing](#7-testing)

---

## 1. Use Cases

### 1.1 Use Case Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           Scarecrow Drone System                                  │
│                                                                                   │
│  ┌────────────────┐                                                              │
│  │ UC1: Map Area  │─────────────┐                                                │
│  │   Operation    │             │                                                │
│  └────────────────┘             │                                                │
│                                 ▼                                                │
│  ┌────────────────┐    ┌──────────────────────────────┐                          │
│  │                │    │                              │                          │
│  │  UC2: Start    │───▶│  UC3: Record Flight Video    │                          │
│  │ Detection      │    │                              │                          │
│  │    Flight      │    └──────────────┬───────────────┘                          │
│  │                │                   │                                          │
│  └───────┬────────┘                   ▼                                          │
│          │            ┌──────────────────────────────┐                           │
│          │            │                              │                           │
│          │            │  UC4: Detect Birds           │                           │
│          │            │                              │                           │
│          │            └──────────────┬───────────────┘                           │
│          │                           │                                           │
│          │                           ▼                                           │
│          │            ┌──────────────────────────────┐                           │
│          │            │                              │                           │
│          │            │  UC5: Chase Birds &          │                           │
│          │            │  Apply Counter Measures      │                           │
│          │            │                              │                           │
│          │            └──────────────┬───────────────┘                           │
│          │                           │                                           │
│          │                           ▼                                           │
│          │            ┌──────────────────────────────┐                           │
│          └───────────▶│                              │                           │
│                       │  UC6: Store Flight Data      │                           │
│                       │                              │                           │
│                       └──────────────┬───────────────┘                           │
│                                      │                                           │
│  ┌────────────────┐                  ▼                                           │
│  │                │    ┌──────────────────────────────┐                          │
│  │  UC7: Abort    │    │                              │                          │
│  │    Mission     │───▶│  UC8: View Flight Results    │                          │
│  │                │    │                              │                          │
│  └────────────────┘    └──────────────────────────────┘                          │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
                    ▲                                    ▲
                    │                                    │
                    │                                    │
              ┌─────┴─────┐                        ┌─────┴─────┐
              │           │                        │           │
              │  Operator │                        │  System   │
              │           │                        │           │
              └───────────┘                        └───────────┘
```

**Google Docs Format:**

+------------------------------------------------------------------------------+
|                         Scarecrow Drone System                               |
|                                                                              |
|  +--------------+                                                            |
|  | UC1: Map Area|--------+                                                   |
|  |  Operation   |        |                                                   |
|  +--------------+        |                                                   |
|                          v                                                   |
|  +--------------+  +---------------------------+                             |
|  |              |  |                           |                             |
|  | UC2: Start   |->| UC3: Record Flight Video  |                             |
|  | Detection    |  |                           |                             |
|  | Flight       |  +-----------+---------------+                             |
|  |              |              |                                             |
|  +------+-------+              v                                             |
|         |         +---------------------------+                              |
|         |         |                           |                              |
|         |         | UC4: Detect Birds         |                              |
|         |         |                           |                              |
|         |         +-----------+---------------+                              |
|         |                     |                                              |
|         |                     v                                              |
|         |         +---------------------------+                              |
|         |         |                           |                              |
|         |         | UC5: Chase Birds &        |                              |
|         |         | Apply Counter Measures    |                              |
|         |         |                           |                              |
|         |         +-----------+---------------+                              |
|         |                     |                                              |
|         |                     v                                              |
|         |         +---------------------------+                              |
|         +-------->|                           |                              |
|                   | UC6: Store Flight Data    |                              |
|                   |                           |                              |
|                   +-----------+---------------+                              |
|                               |                                              |
|  +--------------+             v                                              |
|  |              |  +---------------------------+                             |
|  | UC7: Abort   |  |                           |                             |
|  | Mission      |->| UC8: View Flight Results  |                             |
|  |              |  |                           |                             |
|  +--------------+  +---------------------------+                             |
|                                                                              |
+------------------------------------------------------------------------------+
                  ^                               ^
                  |                               |
                  |                               |
            +-----+-----+                   +-----+-----+
            |           |                   |           |
            | Operator  |                   |  System   |
            |           |                   |           |
            +-----------+                   +-----------+

---

### 1.2 Actors

| Actor | Description |
|-------|-------------|
| Operator | A human user who interacts with the Scarecrow Drone system through the web-based dashboard. The operator can initiate flights, monitor drone status, view flight history, and review bird detection results. |
| System | The automated system components that perform actions without direct user intervention, including the bird detection model, video recording service, and data storage mechanisms. |

### 1.3 Use Cases Summary

| UC | Name | Description | Actor | Using UC |
|----|------|-------------|-------|----------|
| UC1 | Map Area Operation | Performs initial mapping of the target area to define flight boundaries and identify key zones for pigeon detection | Operator | UC6 |
| UC2 | Start Detection Flight | Initiates a drone flight session for active pigeon detection and deterrence operations | Operator | UC3, UC6 |
| UC3 | Record Flight Video | Captures video feed from the drone's camera during flight for bird detection analysis | System | UC4 |
| UC4 | Detect Birds | Analyzes video frames using YOLO model to identify and mark bird (pigeon) locations | System | UC5 |
| UC5 | Chase Birds & Apply Counter Measures | Pursues detected birds and activates deterrent measures (movement patterns, pursuit) to scare them away | System | UC6 |
| UC6 | Store Flight Data | Persists flight information, telemetry data, detection images, and video recordings to the database | System | - |
| UC7 | Abort Mission | Immediately terminates the current flight mission and initiates safe return/landing procedures | Operator | UC6 |
| UC8 | View Flight Results | Displays historical flight records with detection images, statistics, and video recordings | Operator | - |

### 1.4 Detailed Use Case Specifications

#### 1.4.1 UC1: Map Area Operation

| Field | Description |
|-------|-------------|
| **Name** | Map Area Operation |
| **Identifier** | UC1 |
| **Actor** | Operator |
| **Precondition** | 1. The system is running and accessible via web dashboard<br>2. The drone is powered on and within communication range<br>3. No other flight is currently in progress<br>4. Camera feed is available |
| **Postconditions** | 1. Area boundaries are defined and stored<br>2. Flight zones are mapped for patrol routes<br>3. Mapping data is saved for future detection flights |
| **Basic Course** | 1. Operator navigates to the Area Mapping page<br>2. Operator initiates mapping flight<br>3. Drone performs systematic area scan<br>4. System captures and processes terrain data<br>5. Operator reviews and confirms mapped boundaries<br>6. System stores mapping data (UC6) |
| **Alternate Courses** | A1. Communication Lost:<br>&nbsp;&nbsp;A1.1. System alerts operator<br>&nbsp;&nbsp;A1.2. Drone holds position or returns home<br>&nbsp;&nbsp;A1.3. Partial mapping data is saved |
| **Extensions** | E1. Operator can manually adjust boundaries after mapping |

#### 1.4.2 UC2: Start Detection Flight

| Field | Description |
|-------|-------------|
| **Name** | Start Detection Flight |
| **Identifier** | UC2 |
| **Actor** | Operator |
| **Precondition** | 1. The system is running and accessible via web dashboard<br>2. The drone is powered on and within communication range<br>3. No other flight is currently in progress<br>4. Area mapping has been completed (UC1) |
| **Postconditions** | 1. A new flight record is created in the database<br>2. Video recording has started<br>3. Bird detection processing is active<br>4. Flight status is set to "in_progress" |
| **Basic Course** | 1. Operator navigates to the Dashboard page<br>2. Operator clicks "Start Detection Flight" button<br>3. System creates a new flight record with current timestamp<br>4. Drone begins patrolling mapped area<br>5. System initiates video recording (UC3)<br>6. System begins bird detection processing (UC4)<br>7. Dashboard displays real-time flight status |
| **Alternate Courses** | A1. Connection Failure:<br>&nbsp;&nbsp;A1.1. System fails to establish connection<br>&nbsp;&nbsp;A1.2. System displays error message<br>&nbsp;&nbsp;A1.3. Flight record is not created |
| **Extensions** | E1. Operator can view live detection feed during flight |

#### 1.4.3 UC3: Record Flight Video

| Field | Description |
|-------|-------------|
| **Name** | Record Flight Video |
| **Identifier** | UC3 |
| **Actor** | System |
| **Precondition** | 1. Detection flight has been initiated (UC2 completed)<br>2. Camera feed is available<br>3. Storage space is available for video files |
| **Postconditions** | 1. Video file is saved to recordings directory<br>2. Video path is associated with flight record<br>3. Video frames are available for detection processing |
| **Basic Course** | 1. System receives flight start signal<br>2. System initializes FFmpeg video capture<br>3. System begins capturing frames from camera stream<br>4. Frames are passed to detection service (UC4)<br>5. Video is encoded and saved to disk<br>6. Recording continues until flight ends |
| **Alternate Courses** | A1. Camera Unavailable:<br>&nbsp;&nbsp;A1.1. System logs error<br>&nbsp;&nbsp;A1.2. Flight continues without video<br>&nbsp;&nbsp;A1.3. Detection operates on available frames |
| **Extensions** | - |

#### 1.4.4 UC4: Detect Birds

| Field | Description |
|-------|-------------|
| **Name** | Detect Birds |
| **Identifier** | UC4 |
| **Actor** | System |
| **Precondition** | 1. Video frames are being captured (UC3 active)<br>2. YOLO detection model is loaded<br>3. Detection service is initialized |
| **Postconditions** | 1. Bird detections are identified with bounding boxes<br>2. Detection images are saved with annotations<br>3. Detection records are stored in database<br>4. Chase sequence is triggered if birds detected |
| **Basic Course** | 1. System receives video frame from recording service<br>2. Frame is preprocessed for YOLO model<br>3. YOLO model analyzes frame for bird presence<br>4. For each detection above confidence threshold:<br>&nbsp;&nbsp;4.1. Bounding box coordinates are extracted<br>&nbsp;&nbsp;4.2. Detection is drawn on frame<br>&nbsp;&nbsp;4.3. Annotated image is saved<br>5. Detection data is sent to storage service (UC6)<br>6. If birds detected, trigger chase sequence (UC5) |
| **Alternate Courses** | A1. No Birds Detected:<br>&nbsp;&nbsp;A1.1. Frame is processed but no detections recorded<br>&nbsp;&nbsp;A1.2. System continues to next frame |
| **Extensions** | E1. Multiple birds can be detected in single frame |

#### 1.4.5 UC5: Chase Birds & Apply Counter Measures

| Field | Description |
|-------|-------------|
| **Name** | Chase Birds & Apply Counter Measures |
| **Identifier** | UC5 |
| **Actor** | System |
| **Precondition** | 1. Birds have been detected (UC4)<br>2. Drone is in active flight mode<br>3. Counter measure systems are operational |
| **Postconditions** | 1. Drone has pursued detected birds<br>2. Counter measures have been activated<br>3. Chase event is logged |
| **Basic Course** | 1. System receives bird detection coordinates<br>2. Drone calculates pursuit trajectory<br>3. Drone moves toward bird location<br>4. System activates deterrent measures (movement/pursuit)<br>5. System monitors bird response<br>6. Drone returns to patrol route when birds dispersed<br>7. Chase data is stored (UC6) |
| **Alternate Courses** | A1. Birds Out of Range:<br>&nbsp;&nbsp;A1.1. System logs detection but does not pursue<br>&nbsp;&nbsp;A1.2. Drone continues patrol route<br>A2. Battery Low During Chase:<br>&nbsp;&nbsp;A2.1. System aborts chase<br>&nbsp;&nbsp;A2.2. Drone initiates return home |
| **Extensions** | E1. Multiple chase sequences can occur during single flight |

#### 1.4.6 UC6: Store Flight Data

| Field | Description |
|-------|-------------|
| **Name** | Store Flight Data |
| **Identifier** | UC6 |
| **Actor** | System |
| **Precondition** | 1. Database connection is established<br>2. Flight data is available for storage |
| **Postconditions** | 1. Flight record is persisted in flights table<br>2. Detection images are stored in ditection_images table<br>3. Video file path is recorded<br>4. Chase events are logged |
| **Basic Course** | 1. System receives flight data to store<br>2. Flight record is inserted/updated in flights table<br>3. For each detection image:<br>&nbsp;&nbsp;3.1. Image path is recorded<br>&nbsp;&nbsp;3.2. Detection metadata is stored<br>4. For each chase event:<br>&nbsp;&nbsp;4.1. Chase coordinates and duration recorded<br>&nbsp;&nbsp;4.2. Counter measure type logged<br>5. Video recording path is associated with flight<br>6. Flight end time and status are updated on completion |
| **Alternate Courses** | A1. Database Error:<br>&nbsp;&nbsp;A1.1. System logs error<br>&nbsp;&nbsp;A1.2. Data is queued for retry<br>&nbsp;&nbsp;A1.3. User is notified of storage issue |
| **Extensions** | - |

#### 1.4.7 UC7: Abort Mission

| Field | Description |
|-------|-------------|
| **Name** | Abort Mission |
| **Identifier** | UC7 |
| **Actor** | Operator |
| **Precondition** | 1. A flight is currently in progress<br>2. System is responsive to commands |
| **Postconditions** | 1. Current flight operations are terminated<br>2. Drone initiates safe landing or return home<br>3. Flight record is updated with aborted status<br>4. Partial data is preserved |
| **Basic Course** | 1. Operator clicks "Abort Mission" button<br>2. System immediately stops all active operations<br>3. Drone stops current movement/chase<br>4. Drone initiates return-to-home sequence<br>5. Video recording is stopped and saved<br>6. Flight status is updated to "aborted" (UC6)<br>7. Dashboard displays abort confirmation |
| **Alternate Courses** | A1. Communication Lost:<br>&nbsp;&nbsp;A1.1. Drone activates failsafe mode<br>&nbsp;&nbsp;A1.2. Drone auto-lands or returns home<br>&nbsp;&nbsp;A1.3. System retries connection<br>A2. Low Battery During Abort:<br>&nbsp;&nbsp;A2.1. Drone prioritizes immediate landing<br>&nbsp;&nbsp;A2.2. System logs emergency landing event |
| **Extensions** | E1. Operator can specify landing location if within range |

#### 1.4.8 UC8: View Flight Results

| Field | Description |
|-------|-------------|
| **Name** | View Flight Results |
| **Identifier** | UC8 |
| **Actor** | Operator |
| **Precondition** | 1. System is running and accessible<br>2. At least one flight record exists |
| **Postconditions** | 1. Flight history and results are displayed to operator |
| **Basic Course** | 1. Operator navigates to Flight History page<br>2. System retrieves all flight records from database<br>3. Flights are displayed in chronological order<br>4. Each flight shows: ID, start time, end time, status, detection count, chase count<br>5. Operator selects a flight to view details<br>6. System displays detection images in gallery format<br>7. Each image shows annotated bird locations<br>8. Chase events are displayed with timestamps and outcomes |
| **Alternate Courses** | A1. No Flights Available:<br>&nbsp;&nbsp;A1.1. System displays "No flights recorded" message<br>A2. No Detections for Flight:<br>&nbsp;&nbsp;A2.1. System displays "No detections for this flight" |
| **Extensions** | E1. Operator can filter flights by date range<br>E2. Operator can view flight video recording<br>E3. Operator can download detection images<br>E4. Operator can export flight statistics |

---

## 2. System Architecture

### 2.1 Deployment Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Machine                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Web Browser                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │              React Frontend (Port 5173)                          │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
│  │  │  │  Dashboard  │  │   Flight    │  │    Detection Gallery    │  │  │  │
│  │  │  │    Page     │  │   History   │  │                         │  │  │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Ground Station (Server Machine)                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Backend (Port 5000)                         │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │                         Controllers                               │ │  │
│  │  │  ┌───────────────┐  ┌────────────────┐  ┌─────────────────────┐  │ │  │
│  │  │  │    Drone      │  │     Flight     │  │     Connection      │  │ │  │
│  │  │  │  Controller   │  │   Controller   │  │     Controller      │  │ │  │
│  │  │  └───────────────┘  └────────────────┘  └─────────────────────┘  │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │                          Services                                 │ │  │
│  │  │  ┌───────────────┐  ┌────────────────┐  ┌─────────────────────┐  │ │  │
│  │  │  │    Drone      │  │     Flight     │  │     Detection       │  │ │  │
│  │  │  │   Service     │  │    Service     │  │      Service        │  │ │  │
│  │  │  └───────────────┘  └────────────────┘  └─────────────────────┘  │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │                        Repositories                               │ │  │
│  │  │  ┌───────────────┐  ┌────────────────┐                           │ │  │
│  │  │  │    Drone      │  │     Flight     │                           │ │  │
│  │  │  │  Repository   │  │   Repository   │                           │ │  │
│  │  │  └───────────────┘  └────────────────┘                           │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      SQLite Database                                   │  │
│  │              (scarecrow-drone/backend/database.db)                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Detection Module                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    detect.py                                     │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
│  │  │  │   FFmpeg    │  │    YOLO     │  │      OpenCV             │  │  │  │
│  │  │  │  Decoder    │  │   Model     │  │   Processing            │  │  │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      File Storage                                      │  │
│  │  ┌─────────────────┐  ┌─────────────────────────────────────────────┐ │  │
│  │  │   recordings/   │  │              detection_images/              │ │  │
│  │  │  (Video files)  │  │          (Annotated detection frames)       │ │  │
│  │  └─────────────────┘  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
              │                                           ▲
              │ MAVLink Commands                          │ RTP/UDP Video Stream
              │ (Flight control, waypoints,               │ (GStreamer JPEG @ 5000)
              │  arm/disarm, mode changes)                │
              ▼                                           │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Drone (Airborne Unit)                              │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Flight Controller (Pixhawk)                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  ArduPilot Firmware                                              │  │  │
│  │  │  ┌─────────────────────────────┐  ┌─────────────────────────┐  │  │  │
│  │  │  │        MAVLink              │  │    IMU / Sensors        │  │  │  │
│  │  │  │        Protocol             │  │   (Altitude, Attitude)  │  │  │  │
│  │  │  └─────────────────────────────┘  └─────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Companion Computer                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
│  │  │  │  GStreamer  │  │   Camera    │  │    WiFi / Telemetry     │  │  │  │
│  │  │  │  Encoder    │  │  Interface  │  │     Radio Link          │  │  │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Hardware Components                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Camera    │  │   Motors    │  │   Battery   │  │  Deterrent  │  │  │
│  │  │ (640x480)   │  │   (x4/x6)   │  │  (LiPo 4S)  │  │   Module    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Google Docs Format:**

+-----------------------------------------------------------------------------+
|                            Client Machine                                   |
|  +-----------------------------------------------------------------------+  |
|  |                       Web Browser                                     |  |
|  |  +-----------------------------------------------------------------+  |  |
|  |  |            React Frontend (Port 5173)                           |  |  |
|  |  |  +-----------+  +-----------+  +-----------------------+        |  |  |
|  |  |  | Dashboard |  |  Flight   |  |  Detection Gallery    |        |  |  |
|  |  |  |   Page    |  |  History  |  |                       |        |  |  |
|  |  |  +-----------+  +-----------+  +-----------------------+        |  |  |
|  |  +-----------------------------------------------------------------+  |  |
|  +-----------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+
                                  |
                                  | HTTP/REST
                                  v
+-----------------------------------------------------------------------------+
|                      Ground Station (Server Machine)                       |
|  +-----------------------------------------------------------------------+  |
|  |                   FastAPI Backend (Port 5000)                         |  |
|  |  +---------------------------------------------------------------+   |  |
|  |  |                       Controllers                             |   |  |
|  |  |  +-------------+  +--------------+  +------------------+      |   |  |
|  |  |  |   Drone     |  |    Flight    |  |   Connection     |      |   |  |
|  |  |  | Controller  |  |  Controller  |  |   Controller     |      |   |  |
|  |  |  +-------------+  +--------------+  +------------------+      |   |  |
|  |  +---------------------------------------------------------------+   |  |
|  |  +---------------------------------------------------------------+   |  |
|  |  |                        Services                               |   |  |
|  |  |  +-------------+  +--------------+  +------------------+      |   |  |
|  |  |  |   Drone     |  |    Flight    |  |   Detection      |      |   |  |
|  |  |  |  Service    |  |   Service    |  |    Service       |      |   |  |
|  |  |  +-------------+  +--------------+  +------------------+      |   |  |
|  |  +---------------------------------------------------------------+   |  |
|  |  +---------------------------------------------------------------+   |  |
|  |  |                      Repositories                             |   |  |
|  |  |  +-------------+  +--------------+                            |   |  |
|  |  |  |   Drone     |  |    Flight    |                            |   |  |
|  |  |  | Repository  |  |  Repository  |                            |   |  |
|  |  |  +-------------+  +--------------+                            |   |  |
|  |  +---------------------------------------------------------------+   |  |
|  +-----------------------------------------------------------------------+  |
|                                  |                                         |
|                                  v                                         |
|  +-----------------------------------------------------------------------+  |
|  |                      SQLite Database                                  |  |
|  |              (scarecrow-drone/backend/database.db)                    |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                    Detection Module                                   |  |
|  |  +-----------------------------------------------------------------+  |  |
|  |  |                    detect.py                                    |  |  |
|  |  |  +-----------+  +-----------+  +---------------------+          |  |  |
|  |  |  |  FFmpeg   |  |   YOLO    |  |      OpenCV         |          |  |  |
|  |  |  | Decoder   |  |  Model    |  |   Processing        |          |  |  |
|  |  |  +-----------+  +-----------+  +---------------------+          |  |  |
|  |  +-----------------------------------------------------------------+  |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                      File Storage                                     |  |
|  |  +---------------+  +-----------------------------------------+       |  |
|  |  | recordings/   |  |          detection_images/              |       |  |
|  |  | (Video files) |  |    (Annotated detection frames)         |       |  |
|  |  +---------------+  +-----------------------------------------+       |  |
|  +-----------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+
            |                                         ^
            | MAVLink Commands                        | RTP/UDP Video Stream
            | (Flight control, waypoints,             | (GStreamer JPEG @ 5000)
            |  arm/disarm, mode changes)              |
            v                                         |
+-----------------------------------------------------------------------------+
|                         Drone (Airborne Unit)                              |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                   Flight Controller (Pixhawk)                         |  |
|  |  +-----------------------------------------------------------------+  |  |
|  |  |  ArduPilot Firmware                                             |  |  |
|  |  |  +-------------------------+  +----------------------+          |  |  |
|  |  |  |       MAVLink           |  |   IMU / Sensors      |          |  |  |
|  |  |  |       Protocol          |  | (Altitude, Attitude) |          |  |  |
|  |  |  +-------------------------+  +----------------------+          |  |  |
|  |  +-----------------------------------------------------------------+  |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                   Companion Computer                                  |  |
|  |  +-----------------------------------------------------------------+  |  |
|  |  |  +-----------+  +-----------+  +---------------------+          |  |  |
|  |  |  | GStreamer |  |  Camera   |  |  WiFi / Telemetry   |          |  |  |
|  |  |  |  Encoder  |  | Interface |  |   Radio Link        |          |  |  |
|  |  |  +-----------+  +-----------+  +---------------------+          |  |  |
|  |  +-----------------------------------------------------------------+  |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                      Hardware Components                              |  |
|  |  +-----------+  +-----------+  +-----------+  +-------------+        |  |
|  |  |  Camera   |  |  Motors   |  |  Battery  |  | Deterrent   |        |  |
|  |  |(640x480)  |  |  (x4/x6)  |  | (LiPo 4S) |  |   Module    |        |  |
|  |  +-----------+  +-----------+  +-----------+  +-------------+        |  |
|  +-----------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+

---

### 2.2 Communication Protocols

**Table 2.2: Communication Protocols**

| Protocol | Direction | Port | Description |
|----------|-----------|------|-------------|
| RTP/UDP (JPEG) | Drone → Ground Station | 5000 | Live video stream from drone camera via GStreamer |
| MAVLink | Ground Station → Drone | Serial/WiFi | Flight commands, arm/disarm, mode changes |
| MAVLink | Drone → Ground Station | Serial/WiFi | Telemetry data (altitude, battery, attitude) |
| HTTP/REST | Frontend → Backend | 5000 | Web API for flight control and data retrieval |

### 2.3 System Components

#### 2.3.1 Frontend Layer

| Component | Technology | Description |
|-----------|------------|-------------|
| React Application | React 19, TypeScript | Single-page application providing the user interface |
| Dashboard Page | React Component | Main control interface for starting/stopping flights and viewing status |
| Flight History Page | React Component | Displays historical flight records and statistics |
| Detection Gallery | React Component | Shows detection images with bird annotations |
| API Service | TypeScript Module | Handles HTTP communication with backend |

#### 2.3.2 Backend Layer

| Component | Technology | Description |
|-----------|------------|-------------|
| FastAPI Application | Python 3.9, FastAPI | RESTful API server handling all client requests |
| DroneController | Python Class | Handles drone-related API endpoints |
| FlightController | Python Class | Manages flight CRUD operations |
| ConnectionController | Python Class | Handles connection status endpoints |
| DroneService | Python Class | Business logic for drone operations |
| FlightService | Python Class | Business logic for flight management |
| DetectionService | Python Class | Manages bird detection processing |
| FlightRepository | Python Class | Data access layer for flight records |
| DroneRepository | Python Class | Data access layer for drone data |

#### 2.3.3 Detection Module

| Component | Technology | Description |
|-----------|------------|-------------|
| detect.py | Python Script | Main detection processing script |
| YOLO Model | YOLOv8 (best_v4.pt) | Pre-trained model for pigeon detection |
| FFmpeg Stream | FFmpeg | Video capture and encoding |
| OpenCV Processing | OpenCV | Frame manipulation and annotation |

#### 2.3.4 Data Storage

| Component | Technology | Description |
|-----------|------------|-------------|
| SQLite Database | SQLite 3 | Persistent storage for flight and detection data |
| Video Storage | File System | Storage for recorded flight videos |
| Image Storage | File System | Storage for detection images |

#### 2.3.5 Drone (Airborne Unit)

| Component | Technology | Description |
|-----------|------------|-------------|
| Flight Controller | Pixhawk (ArduPilot) | Autopilot system managing flight stabilization, navigation, and sensor fusion |
| Companion Computer | Raspberry Pi / Intel NUC | Handles video streaming, camera interface, and WiFi communication |
| Camera | USB/CSI Camera (640x480) | Captures video for streaming to ground station |
| GStreamer Encoder | GStreamer 1.0 | Encodes and streams video via RTP/UDP to ground station |
| IMU Sensors | Accelerometer, Gyroscope, Barometer | Provides attitude, altitude, and motion data |
| Telemetry Radio | WiFi / SiK Radio | Bidirectional MAVLink communication with ground station |
| Deterrent Module | Counter-Measure Device | Deterrent system for scaring birds away |

---

## 3. Data Model

### 3.1 Class Diagram

```
                    ┌─────────────────────────────────────────┐
                    │               AreaMap                    │
                    ├─────────────────────────────────────────┤
                    │ - id: int                               │
                    │ - name: string                          │
                    │ - created_at: datetime                  │
                    │ - updated_at: datetime                  │
                    │ - boundaries: JSON/string               │
                    │ - area_size: float (sq meters)          │
                    │ - status: string (active/draft)         │
                    ├─────────────────────────────────────────┤
                    │ + create_map(): void                    │
                    │ + update_boundaries(boundaries): void   │
                    │ + validate_boundaries(): bool           │
                    │ + get_boundaries(): JSON                │
                    │ + set_status(status): void              │
                    │ + get_area_size(): float                │
                    └─────────────────────────────────────────┘
                                      │
                                      │ 1
                                      │
                                      │ *
                                      ▼
┌─────────────────────────────────────────┐
│                 Flight                   │
├─────────────────────────────────────────┤
│ - id: int                               │
│ - area_map_id: int (FK)                 │
│ - start_time: datetime                  │
│ - end_time: datetime (nullable)         │
│ - status: string                        │
│ - video_path: string (nullable)         │
├─────────────────────────────────────────┤
│ + start(): void                         │
│ + stop(): void                          │
│ + abort(): void                         │
│ + get_duration(): timedelta             │
│ + get_detection_count(): int            │
│ + get_detections(): List[DetectionImage]│
│ + add_detection(detection): void        │
│ + get_video_path(): string              │
│ + set_video_path(path): void            │
│ + get_telemetry(): Telemetry            │
│ + set_telemetry(telemetry): void        │
│ + get_area_map(): AreaMap               │
│ + set_area_map(area_map): void          │
└─────────────────────────────────────────┘
          │                     │                      │
        1 │                   1 │                    1 │
          │                     │                      │
          │ *                   │ 1                    │ *
          ▼                     ▼                      ▼
┌─────────────────────────────┐  ┌─────────────────────────────────────────┐  ┌─────────────────────────────────────────┐
│      DetectionImage         │  │               Telemetry                  │  │              ChaseEvent                  │
├─────────────────────────────┤  ├─────────────────────────────────────────┤  ├─────────────────────────────────────────┤
│ - id: int                   │  │ - flight_id: int (PK)                   │  │ - id: int                               │
│ - flight_id: int (FK)       │  │ - battery_level: float (nullable)       │  │ - flight_id: int (FK)                   │
│ - image_path: string        │  │ - distance: float                       │  │ - detection_image_id: int (FK)          │
│ - timestamp: datetime       │  │ - detections: int                       │  │ - start_time: datetime                  │
├─────────────────────────────┤  ├─────────────────────────────────────────┤  │ - end_time: datetime                    │
│ + save(): void              │  │ + get_flight(): Flight                  │  │ - counter_measure_type: string          │
│ + get_flight(): Flight      │  │ + update_battery(level): void           │  │ - outcome: string                       │
│ + get_timestamp(): datetime │  │ + add_distance(dist): void              │  ├─────────────────────────────────────────┤
│ + get_image_path(): string  │  │ + increment_detections(): void          │  │ + log_chase(): void                     │
│ + set_image_path(path): void│  └─────────────────────────────────────────┘  │ + get_duration(): timedelta             │
└─────────────────────────────┘                                                │ + get_outcome(): string                 │
          │                                                                    │ + set_outcome(outcome): void            │
        1 │                                                                    └─────────────────────────────────────────┘
          │                                                                                       ▲
          │ 0..1                                                                                  │
          └───────────────────────────────────────────────────────────────────────────────────────┘
```

**Google Docs Format:**

                    +---------------------------------------+
                    |              AreaMap                  |
                    +---------------------------------------+
                    | - id: int                             |
                    | - name: string                        |
                    | - created_at: datetime                |
                    | - updated_at: datetime                |
                    | - boundaries: JSON/string             |
                    | - area_size: float (sq meters)        |
                    | - status: string (active/draft)       |
                    +---------------------------------------+
                    | + create_map(): void                  |
                    | + update_boundaries(boundaries): void |
                    | + validate_boundaries(): bool         |
                    | + get_boundaries(): JSON              |
                    | + set_status(status): void            |
                    | + get_area_size(): float              |
                    +---------------------------------------+
                                    |
                                    | 1
                                    |
                                    | *
                                    v
+---------------------------------------+
|               Flight                  |
+---------------------------------------+
| - id: int                             |
| - area_map_id: int (FK)               |
| - start_time: datetime                |
| - end_time: datetime (nullable)       |
| - status: string                      |
| - video_path: string (nullable)       |
+---------------------------------------+
| + start(): void                       |
| + stop(): void                        |
| + abort(): void                       |
| + get_duration(): timedelta           |
| + get_detection_count(): int          |
| + get_detections(): List[DetectionImage]|
| + add_detection(detection): void      |
| + get_video_path(): string            |
| + set_video_path(path): void          |
| + get_telemetry(): Telemetry          |
| + set_telemetry(telemetry): void      |
| + get_area_map(): AreaMap             |
| + set_area_map(area_map): void        |
+---------------------------------------+
        |                |                    |
      1 |              1 |                  1 |
        |                |                    |
        | *              | 1                  | *
        v                v                    v
+---------------------------+  +---------------------------------------+  +---------------------------------------+
|      DetectionImage       |  |             Telemetry                 |  |            ChaseEvent                 |
+---------------------------+  +---------------------------------------+  +---------------------------------------+
| - id: int                 |  | - flight_id: int (PK)                 |  | - id: int                             |
| - flight_id: int (FK)     |  | - battery_level: float (nullable)     |  | - flight_id: int (FK)                 |
| - image_path: string      |  | - distance: float                     |  | - detection_image_id: int (FK)        |
| - timestamp: datetime     |  | - detections: int                     |  | - start_time: datetime                |
+---------------------------+  +---------------------------------------+  | - end_time: datetime                  |
| + save(): void            |  | + get_flight(): Flight                |  | - counter_measure_type: string        |
| + get_flight(): Flight    |  | + update_battery(level): void         |  | - outcome: string                     |
| + get_timestamp(): datetime| | + add_distance(dist): void            |  +---------------------------------------+
| + get_image_path(): string|  | + increment_detections(): void        |  | + log_chase(): void                   |
| + set_image_path(path): void| +---------------------------------------+  | + get_duration(): timedelta           |
+---------------------------+                                              | + get_outcome(): string               |
        |                                                                  | + set_outcome(outcome): void          |
      1 |                                                                  +---------------------------------------+
        |                                                                                     ^
        | 0..1                                                                                |
        +-------------------------------------------------------------------------------------+

---

### 3.2 Data Objects Relationships

The relationships between data objects are shown below:

```
┌─────────────┐
│   AreaMap   │
└─────────────┘
       │
       │ 1
       │
       │ *
       ▼
┌─────────────┐
│   Flight    │
└─────────────┘
       │
       ├────────────────┬────────────────┐
       │                │                │
     1 │              1 │              1 │
       │                │                │
     * │              1 │              * │
       ▼                ▼                ▼
┌──────────────┐  ┌───────────┐  ┌─────────────┐
│DetectionImage│  │ Telemetry │  │ ChaseEvent  │
└──────────────┘  └───────────┘  └─────────────┘
       │                                 ▲
       │ 1                               │
       │                                 │
       │ 0..1                            │
       └─────────────────────────────────┘
```

**Google Docs Format:**

+-------------+
|   AreaMap   |
+-------------+
       |
       | 1
       |
       | *
       v
+-------------+
|   Flight    |
+-------------+
       |
       +-------------+-------------+
       |             |             |
     1 |           1 |           1 |
       |             |             |
     * |           1 |           * |
       v             v             v
+------------+  +---------+  +------------+
|Detection   |  |Telemetry|  |ChaseEvent  |
|Image       |  |         |  |            |
+------------+  +---------+  +------------+
       |                           ^
       | 1                         |
       |                           |
       | 0..1                      |
       +---------------------------+

---

### 3.3 Databases

#### 3.3.1 Entity Relationship Diagram (ERD)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│    ┌────────────────────────────┐                                           │
│    │        area_maps           │                                           │
│    ├────────────────────────────┤                                           │
│    │ PK  id          INTEGER    │                                           │
│    │     name        TEXT       │                                           │
│    │     created_at  DATETIME   │                                           │
│    │     updated_at  DATETIME   │                                           │
│    │     boundaries  TEXT       │                                           │
│    │     area_size   REAL       │                                           │
│    │     status      TEXT       │                                           │
│    └────────────────────────────┘                                           │
│                │                                                             │
│                │ 1                                                           │
│                │                                                             │
│                │ *                                                           │
│                ▼                                                             │
│    ┌────────────────────────────┐         ┌────────────────────────────┐    │
│    │          flights           │         │     detection_images       │    │
│    ├────────────────────────────┤         ├────────────────────────────┤    │
│    │ PK  id          INTEGER    │────┐    │ PK  id          INTEGER    │    │
│    │ FK  area_map_id INTEGER    │    │    │ FK  flight_id   INTEGER    │◀───┤
│    │     start_time  DATETIME   │    │    │     image_path  TEXT       │    │
│    │     end_time    DATETIME   │    └───▶│     timestamp   DATETIME   │    │
│    │     status      TEXT       │    1  * └────────────────────────────┘    │
│    │     video_path  TEXT       │                         │                 │
│    └────────────────────────────┘                         │ 1               │
│                │                │                          │                 │
│                │ 1              │ 1                        │ 1               │
│                │                │                          │                 │
│                │ 1              │ *                        │ *               │
│                ▼                ▼                          ▼                 │
│    ┌────────────────────────────┐      ┌────────────────────────────────┐   │
│    │         telemetry          │      │         chase_events           │   │
│    ├────────────────────────────┤      ├────────────────────────────────┤   │
│    │ PK/FK flight_id  INTEGER   │      │ PK  id                 INTEGER │   │
│    │     battery_level REAL     │      │ FK  flight_id          INTEGER │   │
│    │     distance     REAL      │      │ FK  detection_image_id INTEGER │   │
│    │     detections   INTEGER   │      │     start_time         DATETIME│   │
│    └────────────────────────────┘      │     end_time           DATETIME│   │
│                                         │     counter_measure_type TEXT  │   │
│                                         │     outcome            TEXT    │   │
│                                         └────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Google Docs Format:**

+------------------------------------------------------------------------------+
|                                                                              |
|    +--------------------------+                                             |
|    |       area_maps          |                                             |
|    +--------------------------+                                             |
|    | PK  id          INTEGER  |                                             |
|    |     name        TEXT     |                                             |
|    |     created_at  DATETIME |                                             |
|    |     updated_at  DATETIME |                                             |
|    |     boundaries  TEXT     |                                             |
|    |     area_size   REAL     |                                             |
|    |     status      TEXT     |                                             |
|    +--------------------------+                                             |
|                |                                                             |
|                | 1                                                           |
|                |                                                             |
|                | *                                                           |
|                v                                                             |
|    +--------------------------+         +--------------------------+         |
|    |        flights           |         |    detection_images      |         |
|    +--------------------------+         +--------------------------+         |
|    | PK  id          INTEGER  |----+    | PK  id          INTEGER  |         |
|    | FK  area_map_id INTEGER  |    |    | FK  flight_id   INTEGER  |<---+    |
|    |     start_time  DATETIME |    |    |     image_path  TEXT     |    |    |
|    |     end_time    DATETIME |    +--->|     timestamp   DATETIME |    |    |
|    |     status      TEXT     |    1  * +--------------------------+    |    |
|    |     video_path  TEXT     |                       |                 |    |
|    +--------------------------+                       | 1               |    |
|                |              |                       |                 |    |
|                | 1            | 1                     | 1               |    |
|                |              |                       |                 |    |
|                | 1            | *                     | *               |    |
|                v              v                       v                 |    |
|    +--------------------------+      +------------------------------+   |    |
|    |       telemetry          |      |       chase_events           |   |    |
|    +--------------------------+      +------------------------------+   |    |
|    | PK/FK flight_id  INTEGER |      | PK  id                INTEGER |   |    |
|    |     battery_level REAL   |      | FK  flight_id         INTEGER |   |    |
|    |     distance     REAL    |      | FK  detection_image_id INTEGER|---+    |
|    |     detections   INTEGER |      |     start_time        DATETIME|        |
|    +--------------------------+      |     end_time          DATETIME|        |
|                                      |     counter_measure_type TEXT |        |
|                                      |     outcome           TEXT    |        |
|                                      +------------------------------+        |
|                                                                              |
+------------------------------------------------------------------------------+

---

#### 3.3.2 Database Tables

##### area_maps Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-increment |
| name | TEXT | No | Name/identifier for the mapped area |
| created_at | DATETIME | No | Timestamp when area map was created |
| updated_at | DATETIME | No | Timestamp when area map was last updated |
| boundaries | TEXT | No | JSON string containing boundary coordinates from LIDAR/image data |
| area_size | REAL | No | Calculated area size in square meters |
| status | TEXT | No | Map status: "active", "draft" |

##### flights Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-increment |
| area_map_id | INTEGER | Yes | Foreign key to area_maps table |
| start_time | DATETIME | No | Timestamp when flight started |
| end_time | DATETIME | Yes | Timestamp when flight ended (null if in progress) |
| status | TEXT | No | Flight status: "in_progress", "completed", "failed", "aborted" |
| video_path | TEXT | Yes | Path to recorded video file |

##### detection_images Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-increment |
| flight_id | INTEGER | No | Foreign key to flights table |
| image_path | TEXT | No | Path to detection image file |
| timestamp | DATETIME | No | Timestamp when detection occurred |

##### telemetry Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| flight_id | INTEGER | No | Primary key and foreign key to flights table (1:1 relationship) |
| battery_level | REAL | Yes | Battery percentage (0-100) |
| distance | REAL | No | Total distance traveled by drone in meters |
| detections | INTEGER | No | Total number of bird detections during flight |

##### chase_events Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-increment |
| flight_id | INTEGER | No | Foreign key to flights table |
| detection_image_id | INTEGER | Yes | Foreign key to detection_images table (optional reference to triggering detection) |
| start_time | DATETIME | No | Timestamp when chase sequence started |
| end_time | DATETIME | Yes | Timestamp when chase sequence ended (null if in progress) |
| counter_measure_type | TEXT | No | Type of counter-measure applied: "pursuit", "movement", "combined" |
| outcome | TEXT | Yes | Chase outcome: "dispersed", "lost", "aborted" |

#### 3.3.3 Main Database Transactions

This section describes the key database transactions, which entities they modify, and how they interact with the database.

##### Transaction 1: Create Flight
**Modified Entities**: `flights`, `telemetry`

**Process**:
1. INSERT new record into `flights` table with `start_time`, `status="in_progress"`, and optional `area_map_id`
2. INSERT new record into `telemetry` table with `flight_id`, initializing `battery_level`, `distance=0`, `detections=0`

##### Transaction 2: Record Detection
**Modified Entities**: `detection_images`, `telemetry`

**Process**:
1. INSERT new record into `detection_images` table with `flight_id`, `image_path`, and `timestamp`
2. UPDATE `telemetry` table, incrementing `detections` count for the associated flight

##### Transaction 3: Log Chase Event
**Modified Entities**: `chase_events`

**Process**:
1. INSERT new record into `chase_events` table with `flight_id`, optional `detection_image_id`, `start_time`, and `counter_measure_type`
2. When chase ends: UPDATE the same record, setting `end_time` and `outcome`

##### Transaction 4: End Flight
**Modified Entities**: `flights`, `telemetry`

**Process**:
1. UPDATE `flights` table, setting `end_time`, `status` (completed/failed/aborted), and `video_path`
2. UPDATE `telemetry` table with final `battery_level` and `distance` values

##### Transaction 5: Create Area Map
**Modified Entities**: `area_maps`

**Process**:
1. INSERT new record into `area_maps` table with `name`, `boundaries`, `area_size`, `status`, `created_at`, and `updated_at`

##### Transaction 6: Update Area Map
**Modified Entities**: `area_maps`

**Process**:
1. UPDATE `area_maps` table, modifying `boundaries`, `area_size`, `status`, and `updated_at` timestamp

---

### 3.4 Database Entity Mapping

All classes in the Class Diagram (Section 3.1) map directly to database entities (tables) in the SQLite database:

- `AreaMap` class → `area_maps` table
- `Flight` class → `flights` table
- `DetectionImage` class → `detection_images` table
- `Telemetry` class → `telemetry` table
- `ChaseEvent` class → `chase_events` table

Each class attribute corresponds to a table column, and the methods in each class provide the business logic for interacting with the database records through the repository pattern.

---

### 3.5 Area Mapping Data Capture

This section describes how the system captures and stores spatial boundary data during the area mapping process.

#### 3.5.1 Mapping Capture Flow Diagram

![Mapping Capture Flow Diagram](diagram_images/Mapping_Capture_Flow.png)

**Figure 3.5.1:** Area Mapping Data Capture Flow - Shows the complete process from operator initiating mapping through GPS coordinate capture to database storage.

---

#### 3.5.2 Boundary Data Structure

The `boundaries` field in the `area_maps` table stores a JSON string containing GPS coordinates that define the mapped area's perimeter.

**Table 3.5.2: Boundary JSON Structure**

| Field | Type | Description |
|-------|------|-------------|
| type | string | Geometry type: "Polygon" |
| coordinates | array | Array of coordinate point arrays |
| coordinates[n] | array | [longitude, latitude] pair for each boundary point |

**Example Boundary JSON:**

```json
{
  "type": "Polygon",
  "coordinates": [
    [34.7818, 32.0853],
    [34.7825, 32.0853],
    [34.7825, 32.0847],
    [34.7818, 32.0847],
    [34.7818, 32.0853]
  ]
}
```

*Note: First and last coordinates are identical to close the polygon.*

---

#### 3.5.3 Mapping Capture Data Table

**Table 3.5.3: Mapping Capture Data Fields**

| Data Element | Source | Storage Field | Processing |
|--------------|--------|---------------|------------|
| GPS Coordinates | Drone GPS sensor | boundaries (JSON) | Collected at each corner/waypoint during mapping flight |
| Polygon Points | Drone flight path | boundaries (JSON) | Ordered sequence of lat/long pairs defining perimeter |
| Area Size | Calculated | area_size (REAL) | Computed from boundary coordinates using geodesic formula |
| Map Name | Operator input | name (TEXT) | User-provided identifier for the area |
| Creation Time | System clock | created_at (DATETIME) | Timestamp when mapping completed |
| Map Status | System | status (TEXT) | Initially "draft", changed to "active" after confirmation |

---

#### 3.5.4 Area Size Calculation

The `area_size` field is calculated from the boundary coordinates using the Shoelace formula adapted for geodesic coordinates:

```
Area Calculation Steps:
1. Convert GPS coordinates to Cartesian (meters)
2. Apply Shoelace formula: A = 0.5 × |Σ(x[i]×y[i+1] - x[i+1]×y[i])|
3. Store result in area_size field (square meters)
```

---

## 4. Behavioral Analysis

This section describes the control flow and behavioral patterns of the Scarecrow Drone system through sequence diagrams, event definitions, and state machine diagrams.

### 4.1 Sequence Diagrams

Sequence diagrams illustrate the interaction between objects and the methods called to accomplish each use case.

#### 4.1.1 UC1: Map Area Operation

```
┌─────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌─────────┐      ┌──────────┐
│Operator │      │Dashboard │      │  Drone   │      │  Drone   │      │ AreaMap │      │ Database │
│         │      │   Page   │      │Controller│      │ Service  │      │         │      │          │
└────┬────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬────┘      └────┬─────┘
     │                │                 │                 │                 │                │
     │ Navigate to    │                 │                 │                 │                │
     │ Area Mapping   │                 │                 │                 │                │
     │───────────────>│                 │                 │                 │                │
     │                │                 │                 │                 │                │
     │ Click "Start   │                 │                 │                 │                │
     │ Mapping"       │                 │                 │                 │                │
     │───────────────>│                 │                 │                 │                │
     │                │                 │                 │                 │                │
     │                │ POST /api/drone/│                 │                 │                │
     │                │   start_mapping │                 │                 │                │
     │                │────────────────>│                 │                 │                │
     │                │                 │                 │                 │                │
     │                │                 │ start_mapping() │                 │                │
     │                │                 │────────────────>│                 │                │
     │                │                 │                 │                 │                │
     │                │                 │                 │ create_map()    │                │
     │                │                 │                 │────────────────>│                │
     │                │                 │                 │                 │                │
     │                │                 │                 │                 │ INSERT area_map│
     │                │                 │                 │                 │───────────────>│
     │                │                 │                 │                 │                │
     │                │                 │                 │                 │ area_map_id    │
     │                │                 │                 │                 │<───────────────│
     │                │                 │                 │                 │                │
     │                │                 │                 │    AreaMap      │                │
     │                │                 │                 │<────────────────│                │
     │                │                 │                 │                 │                │
     │                │                 │   AreaMap       │                 │                │
     │                │                 │<────────────────│                 │                │
     │                │                 │                 │                 │                │
     │                │    200 OK       │                 │                 │                │
     │                │<────────────────│                 │                 │                │
     │                │                 │                 │                 │                │
     │ Mapping        │                 │                 │                 │                │
     │ Successful     │                 │                 │                 │                │
     │<───────────────│                 │                 │                 │                │
     │                │                 │                 │                 │                │
```

**Google Docs Format:**

Operator -> Dashboard: Navigate to Area Mapping
Operator -> Dashboard: Click "Start Mapping"
Dashboard -> DroneController: POST /api/drone/start_mapping
DroneController -> DroneService: start_mapping()
DroneService -> AreaMap: create_map()
AreaMap -> Database: INSERT area_map
Database -> AreaMap: area_map_id
AreaMap -> DroneService: AreaMap
DroneService -> DroneController: AreaMap
DroneController -> Dashboard: 200 OK
Dashboard -> Operator: Mapping Successful

---

**Key Methods:**
- `Dashboard.handleStartMapping()` - Initiates mapping request
- `DroneController.start_mapping()` - API endpoint handler
- `DroneService.start_mapping()` - Business logic for mapping
- `AreaMap.create_map()` - Creates new area map record
- `Database.INSERT()` - Persists area map data

---

#### 4.1.2 UC2: Start Detection Flight

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐
│Operator │   │Dashboard │   │  Flight  │   │  Flight  │   │ Flight │   │ Database │
│         │   │   Page   │   │Controller│   │ Service  │   │        │   │          │
└────┬────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └───┬────┘   └────┬─────┘
     │             │              │              │              │             │
     │ Click "Start│              │              │              │             │
     │  Flight"    │              │              │              │             │
     │────────────>│              │              │              │             │
     │             │              │              │              │             │
     │             │ POST /api/   │              │              │             │
     │             │   flights    │              │              │             │
     │             │─────────────>│              │              │             │
     │             │              │              │              │             │
     │             │              │create_flight()│             │             │
     │             │              │─────────────>│              │             │
     │             │              │              │              │             │
     │             │              │              │ start()      │             │
     │             │              │              │─────────────>│             │
     │             │              │              │              │             │
     │             │              │              │              │INSERT flight│
     │             │              │              │              │────────────>│
     │             │              │              │              │             │
     │             │              │              │              │INSERT       │
     │             │              │              │              │telemetry    │
     │             │              │              │              │────────────>│
     │             │              │              │              │             │
     │             │              │              │              │ flight_id   │
     │             │              │              │              │<────────────│
     │             │              │              │              │             │
     │             │              │              │    Flight    │             │
     │             │              │              │<─────────────│             │
     │             │              │              │              │             │
     │             │              │    Flight    │              │             │
     │             │              │<─────────────│              │             │
     │             │              │              │              │             │
     │             │   201 Created│              │              │             │
     │             │<─────────────│              │              │             │
     │             │              │              │              │             │
     │ Flight      │              │              │              │             │
     │ Started     │              │              │              │             │
     │<────────────│              │              │              │             │
     │             │              │              │              │             │
```

**Google Docs Format:**

Operator -> Dashboard: Click "Start Flight"
Dashboard -> FlightController: POST /api/flights
FlightController -> FlightService: create_flight()
FlightService -> Flight: start()
Flight -> Database: INSERT flight
Flight -> Database: INSERT telemetry
Database -> Flight: flight_id
Flight -> FlightService: Flight
FlightService -> FlightController: Flight
FlightController -> Dashboard: 201 Created
Dashboard -> Operator: Flight Started

---

**Key Methods:**
- `Dashboard.handleStartFlight()` - Initiates flight
- `FlightController.create()` - API endpoint handler
- `FlightService.create_flight()` - Business logic
- `Flight.start()` - Creates flight record
- `Database.INSERT()` - Persists flight and telemetry

#### 4.1.3 UC3: Record Flight Video

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Flight  │   │  Video   │   │  FFmpeg  │   │   File   │   │ Database │
│ Service  │   │ Recorder │   │ Process  │   │  System  │   │          │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │              │
     │ start_       │              │              │              │
     │ recording()  │              │              │              │
     │─────────────>│              │              │              │
     │              │              │              │              │
     │              │ initialize_  │              │              │
     │              │  ffmpeg()    │              │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │    ready     │              │              │
     │              │<─────────────│              │              │
     │              │              │              │              │
     │              │ capture_     │              │              │
     │              │  frame()     │              │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │    frame     │              │              │
     │              │<─────────────│              │              │
     │              │              │              │              │
     │              │ encode_video()              │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │              │ write_file() │              │
     │              │              │─────────────>│              │
     │              │              │              │              │
     │              │              │   success    │              │
     │              │              │<─────────────│              │
     │              │              │              │              │
     │              │              │              │              │
     │              │ save_video_  │              │              │
     │              │  path()      │              │              │
     │              │──────────────────────────────────────────>│
     │              │              │              │              │
     │              │              │              │    success   │
     │              │<──────────────────────────────────────────│
     │              │              │              │              │
     │   success    │              │              │              │
     │<─────────────│              │              │              │
     │              │              │              │              │
```

**Google Docs Format:**

FlightService -> VideoRecorder: start_recording()
VideoRecorder -> FFmpegProcess: initialize_ffmpeg()
FFmpegProcess -> VideoRecorder: ready
VideoRecorder -> FFmpegProcess: capture_frame()
FFmpegProcess -> VideoRecorder: frame
VideoRecorder -> FFmpegProcess: encode_video()
FFmpegProcess -> FileSystem: write_file()
FileSystem -> FFmpegProcess: success
VideoRecorder -> Database: save_video_path()
Database -> VideoRecorder: success
VideoRecorder -> FlightService: success

---

**Key Methods:**
- `FlightService.start_recording()` - Initiates video capture
- `VideoRecorder.initialize_ffmpeg()` - Sets up FFmpeg stream
- `FFmpegProcess.capture_frame()` - Captures video frames
- `FFmpegProcess.encode_video()` - Encodes video stream
- `FileSystem.write_file()` - Saves video to disk
- `Database.UPDATE()` - Updates flight record with video path

---

#### 4.1.4 UC4: Detect Birds

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Video   │   │Detection │   │   YOLO   │   │Detection │   │   File   │   │ Database │
│ Recorder │   │ Service  │   │  Model   │   │  Image   │   │  System  │   │          │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │              │              │
     │ send_frame() │              │              │              │              │
     │─────────────>│              │              │              │              │
     │              │              │              │              │              │
     │              │ preprocess_  │              │              │              │
     │              │  frame()     │              │              │              │
     │              │─────────────>│              │              │              │
     │              │              │              │              │              │
     │              │   frame      │              │              │              │
     │              │<─────────────│              │              │              │
     │              │              │              │              │              │
     │              │ detect()     │              │              │              │
     │              │─────────────>│              │              │              │
     │              │              │              │              │              │
     │              │  detections  │              │              │              │
     │              │<─────────────│              │              │              │
     │              │              │              │              │              │
     │              │ draw_        │              │              │              │
     │              │  bboxes()    │              │              │              │
     │              │──────────────────────────>│              │              │
     │              │              │              │              │              │
     │              │              │   annotated_image           │              │
     │              │<──────────────────────────│              │              │
     │              │              │              │              │              │
     │              │ save()       │              │              │              │
     │              │──────────────────────────>│              │              │
     │              │              │              │              │              │
     │              │              │              │ write_image()│              │
     │              │              │              │─────────────>│              │
     │              │              │              │              │              │
     │              │              │              │   success    │              │
     │              │              │              │<─────────────│              │
     │              │              │              │              │              │
     │              │              │              │ INSERT       │              │
     │              │              │              │ detection_   │              │
     │              │              │              │ image        │              │
     │              │              │              │─────────────────────────────>│
     │              │              │              │              │              │
     │              │              │              │              │UPDATE        │
     │              │              │              │              │telemetry     │
     │              │              │              │              │(detections++) │
     │              │              │              │              │─────────────>│
     │              │              │              │              │              │
     │              │              │              │              │   success    │
     │              │              │              │<─────────────────────────────│
     │              │              │              │              │              │
     │              │ DetectionImage              │              │              │
     │              │<──────────────────────────│              │              │
     │              │              │              │              │              │
```

**Google Docs Format:**

VideoRecorder -> DetectionService: send_frame()
DetectionService -> YOLOModel: preprocess_frame()
YOLOModel -> DetectionService: frame
DetectionService -> YOLOModel: detect()
YOLOModel -> DetectionService: detections
DetectionService -> DetectionImage: draw_bboxes()
DetectionImage -> DetectionService: annotated_image
DetectionService -> DetectionImage: save()
DetectionImage -> FileSystem: write_image()
FileSystem -> DetectionImage: success
DetectionImage -> Database: INSERT detection_image
DetectionImage -> Database: UPDATE telemetry (detections++)
Database -> DetectionImage: success
DetectionImage -> DetectionService: DetectionImage

---

**Key Methods:**
- `VideoRecorder.send_frame()` - Sends frame for detection
- `DetectionService.preprocess_frame()` - Prepares frame for YOLO
- `YOLOModel.detect()` - Performs bird detection
- `DetectionImage.draw_bboxes()` - Annotates image with bounding boxes
- `DetectionImage.save()` - Saves detection image
- `FileSystem.write_image()` - Writes image to disk
- `Database.INSERT()` - Records detection in database
- `Database.UPDATE()` - Increments detection count in telemetry

#### 4.1.5 UC5: Chase Birds & Apply Counter Measures

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Detection │   │  Drone   │   │  Drone   │   │  Chase   │   │ Database │
│ Service  │   │Controller│   │ Service  │   │  Event   │   │          │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │              │
     │ bird_        │              │              │              │
     │ detected()   │              │              │              │
     │─────────────>│              │              │              │
     │              │              │              │              │
     │              │ initiate_    │              │              │
     │              │  chase()     │              │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │              │ log_chase()  │              │
     │              │              │─────────────>│              │
     │              │              │              │              │
     │              │              │              │INSERT chase_ │
     │              │              │              │event         │
     │              │              │              │─────────────>│
     │              │              │              │              │
     │              │              │              │  chase_id    │
     │              │              │              │<─────────────│
     │              │              │              │              │
     │              │              │ calculate_   │              │
     │              │              │ trajectory() │              │
     │              │              │─────────────────────────────┐
     │              │              │              │              │
     │              │              │<─────────────────────────────
     │              │              │              │              │
     │              │              │ move_to_     │              │
     │              │              │ location()   │              │
     │              │              │──────────────────────────────┐
     │              │              │              │              │
     │              │              │<──────────────────────────────
     │              │              │              │              │
     │              │              │ activate_    │              │
     │              │              │ countermeasure()            │
     │              │              │──────────────────────────────┐
     │              │              │              │              │
     │              │              │<──────────────────────────────
     │              │              │              │              │
     │              │              │ return_to_   │              │
     │              │              │ patrol()     │              │
     │              │              │──────────────────────────────┐
     │              │              │              │              │
     │              │              │<──────────────────────────────
     │              │              │              │              │
     │              │              │ set_outcome()│              │
     │              │              │─────────────>│              │
     │              │              │              │              │
     │              │              │              │UPDATE chase_ │
     │              │              │              │event         │
     │              │              │              │─────────────>│
     │              │              │              │              │
     │              │              │              │  success     │
     │              │              │              │<─────────────│
     │              │              │              │              │
     │              │   success    │              │              │
     │              │<─────────────│              │              │
     │              │              │              │              │
```

**Google Docs Format:**

DetectionService -> DroneController: bird_detected()
DroneController -> DroneService: initiate_chase()
DroneService -> ChaseEvent: log_chase()
ChaseEvent -> Database: INSERT chase_event
Database -> ChaseEvent: chase_id
DroneService -> DroneService: calculate_trajectory()
DroneService -> DroneService: move_to_location()
DroneService -> DroneService: activate_countermeasure()
DroneService -> DroneService: return_to_patrol()
DroneService -> ChaseEvent: set_outcome()
ChaseEvent -> Database: UPDATE chase_event
Database -> ChaseEvent: success
DroneService -> DroneController: success

---

**Key Methods:**
- `DetectionService.bird_detected()` - Triggers chase
- `DroneController.initiate_chase()` - Starts chase sequence
- `DroneService.initiate_chase()` - Business logic
- `ChaseEvent.log_chase()` - Creates chase record
- `DroneService.calculate_trajectory()` - Plans pursuit path
- `DroneService.move_to_location()` - Executes movement
- `DroneService.activate_countermeasure()` - Activates deterrent
- `DroneService.return_to_patrol()` - Returns to patrol route
- `ChaseEvent.set_outcome()` - Records chase result
- `Database.INSERT()` - Creates chase event
- `Database.UPDATE()` - Updates chase outcome

---

#### 4.1.6 UC6: Store Flight Data

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Flight  │   │  Flight  │   │  Flight  │   │ Database │
│Controller│   │ Service  │   │Repository│   │          │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
     │ PUT /api/    │              │              │
     │ flights/{id} │              │              │
     │─────────────>│              │              │
     │              │              │              │
     │              │ update_      │              │
     │              │ flight()     │              │
     │              │─────────────>│              │
     │              │              │              │
     │              │              │ UPDATE flight│
     │              │              │─────────────>│
     │              │              │              │
     │              │              │ UPDATE       │
     │              │              │ telemetry    │
     │              │              │─────────────>│
     │              │              │              │
     │              │              │   success    │
     │              │              │<─────────────│
     │              │              │              │
     │              │    Flight    │              │
     │              │<─────────────│              │
     │              │              │              │
     │    200 OK    │              │              │
     │<─────────────│              │              │
     │              │              │              │
```

**Key Methods:**
- `FlightController.update()` - API endpoint
- `FlightService.update_flight()` - Business logic
- `FlightRepository.update()` - Data access
- `Database.UPDATE()` - Persists flight data
- `Database.UPDATE()` - Updates telemetry

#### 4.1.7 UC7: Abort Mission

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Operator │   │Dashboard │   │  Flight  │   │  Flight  │   │  Drone   │   │ Database │
│         │   │   Page   │   │Controller│   │ Service  │   │ Service  │   │          │
└────┬────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │             │              │              │              │              │
     │ Click "Abort│              │              │              │              │
     │  Mission"   │              │              │              │              │
     │────────────>│              │              │              │              │
     │             │              │              │              │              │
     │             │ POST /api/   │              │              │              │
     │             │ flights/{id}/│              │              │              │
     │             │   abort      │              │              │              │
     │             │─────────────>│              │              │              │
     │             │              │              │              │              │
     │             │              │ abort_flight()              │              │
     │             │              │─────────────>│              │              │
     │             │              │              │              │              │
     │             │              │              │ stop_        │              │
     │             │              │              │ operations() │              │
     │             │              │              │─────────────>│              │
     │             │              │              │              │              │
     │             │              │              │ stop_        │              │
     │             │              │              │ recording()  │              │
     │             │              │              │─────────────>│              │
     │             │              │              │              │              │
     │             │              │              │   success    │              │
     │             │              │              │<─────────────│              │
     │             │              │              │              │              │
     │             │              │              │ return_home()│              │
     │             │              │              │─────────────>│              │
     │             │              │              │              │              │
     │             │              │              │   success    │              │
     │             │              │              │<─────────────│              │
     │             │              │              │              │              │
     │             │              │              │ UPDATE flight│              │
     │             │              │              │ status=      │              │
     │             │              │              │ "aborted"    │              │
     │             │              │              │─────────────────────────────>│
     │             │              │              │              │              │
     │             │              │              │              │   success    │
     │             │              │              │<─────────────────────────────│
     │             │              │              │              │              │
     │             │              │    Flight    │              │              │
     │             │              │<─────────────│              │              │
     │             │              │              │              │              │
     │             │   200 OK     │              │              │              │
     │             │<─────────────│              │              │              │
     │             │              │              │              │              │
     │ Mission     │              │              │              │              │
     │ Aborted     │              │              │              │              │
     │<────────────│              │              │              │              │
     │             │              │              │              │              │
```

**Key Methods:**
- `Dashboard.handleAbort()` - Initiates abort
- `FlightController.abort()` - API endpoint
- `FlightService.abort_flight()` - Business logic
- `DroneService.stop_operations()` - Stops all operations
- `DroneService.stop_recording()` - Stops video
- `DroneService.return_home()` - Returns drone
- `Database.UPDATE()` - Sets flight status to "aborted"

#### 4.1.8 UC8: View Flight Results

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Operator │   │  Flight  │   │  Flight  │   │  Flight  │   │ Database │
│         │   │ History  │   │Controller│   │ Service  │   │          │
└────┬────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │             │              │              │              │
     │ Navigate to │              │              │              │
     │ Flight      │              │              │              │
     │ History     │              │              │              │
     │────────────>│              │              │              │
     │             │              │              │              │
     │             │ GET /api/    │              │              │
     │             │  flights     │              │              │
     │             │─────────────>│              │              │
     │             │              │              │              │
     │             │              │ get_all_     │              │
     │             │              │ flights()    │              │
     │             │              │─────────────>│              │
     │             │              │              │              │
     │             │              │              │ SELECT flights
     │             │              │              │─────────────>│
     │             │              │              │              │
     │             │              │              │  List[Flight]│
     │             │              │              │<─────────────│
     │             │              │              │              │
     │             │              │ List[Flight] │              │
     │             │              │<─────────────│              │
     │             │              │              │              │
     │             │  200 OK +    │              │              │
     │             │  flights     │              │              │
     │             │<─────────────│              │              │
     │             │              │              │              │
     │ Display     │              │              │              │
     │ Flights     │              │              │              │
     │<────────────│              │              │              │
     │             │              │              │              │
     │ Select      │              │              │              │
     │ Flight      │              │              │              │
     │────────────>│              │              │              │
     │             │              │              │              │
     │             │ GET /api/    │              │              │
     │             │ flights/{id}/│              │              │
     │             │  detections  │              │              │
     │             │─────────────>│              │              │
     │             │              │              │              │
     │             │              │ get_flight_  │              │
     │             │              │ detections() │              │
     │             │              │─────────────>│              │
     │             │              │              │              │
     │             │              │              │SELECT        │
     │             │              │              │detection_    │
     │             │              │              │images        │
     │             │              │              │─────────────>│
     │             │              │              │              │
     │             │              │              │  List[       │
     │             │              │              │  Detection   │
     │             │              │              │  Image]      │
     │             │              │              │<─────────────│
     │             │              │              │              │
     │             │              │ List[        │              │
     │             │              │ DetectionImage]             │
     │             │              │<─────────────│              │
     │             │              │              │              │
     │             │  200 OK +    │              │              │
     │             │  detections  │              │              │
     │             │<─────────────│              │              │
     │             │              │              │              │
     │ Display     │              │              │              │
     │ Detection   │              │              │              │
     │ Gallery     │              │              │              │
     │<────────────│              │              │              │
     │             │              │              │              │
```

**Key Methods:**
- `FlightHistory.componentDidMount()` - Loads flights on page load
- `FlightController.get_all()` - API endpoint for all flights
- `FlightService.get_all_flights()` - Business logic
- `Database.SELECT()` - Retrieves flight records
- `FlightHistory.onFlightSelect()` - Handles flight selection
- `FlightController.get_detections()` - API endpoint for detections
- `FlightService.get_flight_detections()` - Business logic
- `Database.SELECT()` - Retrieves detection images

---

### 4.2 Event Table

The Scarecrow Drone system is event-driven, responding to various system and user events. Below are the key events that govern system behavior.

#### 4.2.1 Drone Events

**Table 4.2.1: Drone Events**

| Event | Trigger | System Response | State Changes |
|-------|---------|-----------------|---------------|
| **Connection Established** | Successful MAVLink connection to drone | - Update connection status to "connected"<br>- Enable flight controls<br>- Start telemetry monitoring | Drone Connection: `disconnected` → `connected` |
| **Connection Lost** | MAVLink connection timeout or failure | - Update connection status to "disconnected"<br>- Disable flight controls<br>- Trigger failsafe if flight in progress<br>- Log connection error | Drone Connection: `connected` → `disconnected`<br>Flight: `in_progress` → `aborted` (if active) |
| **Battery Low** | Battery level drops below 20% threshold | - Alert operator with warning message<br>- If in chase, abort chase immediately<br>- Initiate return-to-home sequence<br>- Log battery warning event | Flight: `in_progress` → `returning_home` |
| **Failsafe Triggered** | Loss of communication or critical error | - Drone automatically lands or returns home<br>- Stop all operations<br>- Save partial data<br>- Log failsafe event | Flight: `in_progress` → `failsafe`<br>Drone: `any_state` → `failsafe_mode` |
| **Camera Feed Available** | Video stream successfully connected | - Enable detection processing<br>- Start video recording<br>- Update camera status | Video Recording: `idle` → `recording` |
| **Camera Feed Lost** | Video stream disconnected or timeout | - Disable detection processing<br>- Stop video recording<br>- Alert operator<br>- Flight continues with telemetry only | Video Recording: `recording` → `stopped`<br>Detection: `processing` → `idle` |

#### 4.2.2 Area Mapping Events

**Table 4.2.2: Area Mapping Events**

| Event | Trigger | System Response | State Changes |
|-------|---------|-----------------|---------------|
| **Mapping Started** | Operator clicks "Start Mapping" button | - Create new area map record in database<br>- Initialize drone for mapping flight<br>- Start camera feed for terrain capture<br>- Update UI to show mapping status | AreaMap: `draft` → `mapping_in_progress` |
| **Terrain Data Captured** | Drone completes area scan | - Process captured terrain/boundary data<br>- Calculate area size<br>- Store boundary coordinates | AreaMap: `mapping_in_progress` → `processing` |
| **Mapping Completed** | Operator confirms mapped boundaries | - Finalize area map record<br>- Set status to "active"<br>- Store mapping data for future flights<br>- Enable detection flights for this area | AreaMap: `processing` → `active` |
| **Mapping Aborted** | Communication lost or operator cancels | - Save partial mapping data<br>- Set status to "draft"<br>- Alert operator<br>- Log abort event | AreaMap: `mapping_in_progress` → `draft` |
| **Boundaries Adjusted** | Operator manually adjusts mapped boundaries | - Update boundary coordinates<br>- Recalculate area size<br>- Update timestamp<br>- Save changes to database | AreaMap: `active` → `active` (updated) |

#### 4.2.3 Flight Events

**Table 4.2.3: Flight Events**

| Event | Trigger | System Response | State Changes |
|-------|---------|-----------------|---------------|
| **Flight Started** | Operator clicks "Start Flight" button | - Create new flight record in database<br>- Initialize telemetry tracking<br>- Start video recording<br>- Begin detection processing<br>- Update UI to show flight status | Flight: `not_started` → `in_progress`<br>Video: `idle` → `recording`<br>Detection: `idle` → `active` |
| **Flight Ended** | Operator clicks "Stop Flight" button | - Stop video recording<br>- Stop detection processing<br>- Update flight record with end time<br>- Save final telemetry data<br>- Set flight status to "completed" | Flight: `in_progress` → `completed`<br>Video: `recording` → `stopped`<br>Detection: `active` → `idle` |
| **Flight Aborted** | Operator clicks "Abort Mission" or system error | - Immediately stop all operations<br>- Drone returns home or lands<br>- Save partial data<br>- Set flight status to "aborted"<br>- Alert operator | Flight: `in_progress` → `aborted`<br>Drone: `any_state` → `returning_home` |
| **Video Recording Started** | Flight started or camera feed available | - Initialize FFmpeg stream<br>- Begin capturing frames<br>- Create video file path<br>- Update flight record with video path | Video: `idle` → `recording` |
| **Video Recording Stopped** | Flight ended or camera feed lost | - Stop FFmpeg stream<br>- Finalize and save video file<br>- Update flight record with final video path | Video: `recording` → `stopped` |
| **Video Recording Failed** | FFmpeg error or storage full | - Log error message<br>- Alert operator<br>- Flight continues without video<br>- Set video status to "failed" | Video: `recording` → `failed` |

#### 4.2.4 Detection Events

**Table 4.2.4: Detection Events**

| Event | Trigger | System Response | State Changes |
|-------|---------|-----------------|---------------|
| **Bird Detected** | YOLO model detects bird with confidence > threshold | - Extract bounding box coordinates<br>- Annotate frame with detection<br>- Save detection image<br>- Increment detection count in telemetry<br>- Trigger chase sequence<br>- Log detection event | Detection: `scanning` → `bird_detected`<br>Chase: `idle` → `initiating` |
| **No Detection in Frame** | YOLO model processes frame with no birds detected | - Continue to next frame<br>- No action taken | Detection: `scanning` → `scanning` |
| **Frame Processed** | Detection service completes frame analysis | - Return frame to video stream<br>- Continue processing next frame | Detection: `processing_frame` → `scanning` |
| **Multiple Birds Detected** | YOLO model detects multiple birds in single frame | - Create separate detection record for each bird<br>- Save annotated image with all detections<br>- Calculate pursuit priority (closest bird)<br>- Trigger chase for highest priority target | Detection: `scanning` → `multiple_birds_detected`<br>Chase: `idle` → `initiating` |
| **Detection Confidence Threshold Met** | Detection confidence score exceeds configured threshold | - Confirm detection as valid<br>- Proceed with detection recording and chase | Detection: `uncertain` → `confirmed` |

#### 4.2.5 Chase Events

**Table 4.2.5: Chase Events**

| Event | Trigger | System Response | State Changes |
|-------|---------|-----------------|---------------|
| **Chase Initiated** | Bird detected during flight | - Create chase event record<br>- Calculate pursuit trajectory<br>- Move drone toward bird location<br>- Log chase start time | Chase: `idle` → `pursuing` |
| **Chase Completed** | Birds dispersed or chase timeout reached | - Stop pursuit<br>- Return to patrol route<br>- Update chase event with end time<br>- Set chase outcome | Chase: `pursuing` → `completed` |
| **Birds Dispersed** | Birds leave area during chase | - Record successful outcome<br>- Return to patrol<br>- Log dispersion event | Chase: `pursuing` → `completed` (outcome: "dispersed") |
| **Birds Lost** | Birds move out of camera range | - Record unsuccessful outcome<br>- Return to patrol<br>- Log lost event | Chase: `pursuing` → `completed` (outcome: "lost") |
| **Counter-Measure Activated (Pursuit)** | Chase sequence reaches target location | - Execute aggressive pursuit<br>- Apply deterrent maneuver<br>- Log counter-measure type | Chase: `pursuing` → `applying_countermeasure` |
| **Counter-Measure Activated (Movement)** | Chase sequence uses movement pattern | - Execute aggressive flight maneuver<br>- Log counter-measure type | Chase: `pursuing` → `applying_countermeasure` |

#### 4.2.6 System Events

**Table 4.2.6: System Events**

| Event | Trigger | System Response | State Changes |
|-------|---------|-----------------|---------------|
| **Shutdown Signal** | System receives shutdown command (SIGTERM/SIGINT) | - Write shutdown message to system logger<br>- Save all open buffers<br>- Close all open files (user files, system files, config files)<br>- Stop video recording gracefully<br>- Update flight status to "aborted" if in progress<br>- Close database connections<br>- Terminate all processes | System: `running` → `shutting_down` → `stopped`<br>Flight: `in_progress` → `aborted` |
| **Database Error** | Database query fails or connection lost | - Log error with details<br>- Queue data for retry<br>- Alert operator via UI notification<br>- Continue operations if possible | Database: `connected` → `error` |
| **Storage Full** | Disk space below threshold | - Alert operator with critical warning<br>- Stop video recording<br>- Continue detection with image saving disabled<br>- Log storage error | Storage: `available` → `full`<br>Video: `recording` → `stopped` |
| **Camera Unavailable** | Camera initialization fails | - Log camera error<br>- Alert operator<br>- Disable flight start until camera available | Camera: `available` → `unavailable`<br>Flight: `start_disabled` |
| **Model Loading Failed** | YOLO model fails to load on startup | - Log critical error<br>- Disable detection functionality<br>- Alert operator<br>- System enters degraded mode | Detection: `initializing` → `failed`<br>System: `starting` → `degraded` |
| **FFmpeg Initialization Failed** | FFmpeg process fails to start | - Log FFmpeg error<br>- Disable video recording<br>- Detection can continue with live stream<br>- Alert operator | Video: `initializing` → `failed` |

#### 4.2.7 Example Event Scenario

**Scenario: Shutdown Signal During Active Flight**

Upon receiving a shutdown signal (SIGTERM), the system performs the following sequence:

1. **Event Detected**: System receives shutdown signal
2. **Logger Notification**: Write "System shutdown initiated" message to system logger
3. **Flight Check**: Determine if flight is in progress
4. **Active Flight Handling**:
   - Stop detection processing immediately
   - Stop video recording and finalize video file
   - Update flight status to "aborted"
   - Save final telemetry data (battery level, distance, detection count)
   - Command drone to return home
5. **Buffer Management**: Save all open buffers to disk
6. **File Closure**: Close all open files:
   - User files (video recordings)
   - System files (logs, temporary files)
   - Configuration files (settings, area maps)
7. **Database Finalization**:
   - Commit all pending transactions
   - Close database connection
8. **Process Termination**: Gracefully terminate all child processes
9. **System Exit**: Exit with code 0

**State Transitions**:
- System: `running` → `shutting_down` → `stopped`
- Flight: `in_progress` → `aborted`
- Video: `recording` → `stopped`
- Detection: `active` → `idle`
- Database: `connected` → `closed`

---

### 4.3 State Machines

This section describes the state machines for key entities in the Scarecrow Drone system.

#### 4.3.1 Flight State Machine

The Flight entity transitions through the following states during its lifecycle:

```
                                           ┌─────────────────┐
                                           │   Connection    │
                                           │     Lost        │
                                           │                 │
                                           └────────┬────────┘
                                                    │
                                                    │ Failsafe
                                                    ▼
        ●──────────────────────────────────────────────────────────--┐
        │                                                            │
        │ Start Flight                                               │
        ▼                                                            │
┌───────────────┐                                                    │
│               │ Stop Flight                                        │
│  In Progress  │──────────────────────────────────────-─┐           │
│               │                                        │           │
└───────┬───────┘                                        │           │
        │                                                │           │
        │ Abort Mission / Battery Low                    │           │
        │                                                │           │
        ▼                                                ▼           │
┌───────────────┐                                  ┌───────────┐     │
│               │                                  │           │     │
│    Aborted    │                                  │ Completed │     │
│               │                                  │           │     │
└───────────────┘                                  └───────────┘     │
        │                                                │           │
        │                                                │           │
        └────────────────────┬───────────────────────────┘           │
                             │                                       │
                             │                                       │
                             ▼                                       │
                      ┌─────────────┐                                │
                      │             │                                │
                      │   Failed    │◀───────────────────────────────┘
                      │             │  System Error
                      └─────────────┘
                             │
                             │
                             ▼
                            ◉
```

**States**:
- **● (Initial)**: Flight not yet started
- **In Progress**: Flight is actively running, detection and video recording active
- **Aborted**: Flight was manually aborted by operator or system (battery low, connection lost)
- **Completed**: Flight ended normally by operator
- **Failed**: Flight failed due to system error or critical failure
- **◉ (Final)**: Flight record finalized

**Transitions**:
| From State | Event | To State |
|------------|-------|----------|
| Initial | Operator clicks "Start Flight" | In Progress |
| In Progress | Operator clicks "Stop Flight" | Completed |
| In Progress | Operator clicks "Abort Mission" | Aborted |
| In Progress | Battery Low warning | Aborted |
| In Progress | Connection Lost | Aborted |
| In Progress | System Error | Failed |
| Completed | N/A (Terminal) | Final |
| Aborted | N/A (Terminal) | Final |
| Failed | N/A (Terminal) | Final |

#### 4.3.2 Drone Connection State Machine

The Drone Connection manages the communication link between ground station and drone:

```
        ●
        │
        │ System Start
        ▼
┌───────────────┐
│               │ Connect Command
│ Disconnected  │────────────────────────────-────┐
│               │                                 │
└───────┬───────┘                                 │
        │                                         │
        │ Retry After Error                       │
        │                                         │
        │                                         ▼
        │                                  ┌─────────────┐
        │                                  │             │
        │                 Connection Lost  │ Connecting  │
        └──────────────────────────────────│             │
                                           └──────┬──────┘
                                                  │
                                                  │ MAVLink Handshake Success
                                                  ▼
                                          ┌───────────────┐
                                          │               │
                 ┌────────────────────────│   Connected   │
                 │                        │               │
                 │ Disconnect Command /   └───────────────┘
                 │ Connection Timeout              │
                 │                                 │ Communication Error
                 │                                 ▼
                 │                          ┌─────────────┐
                 └─────────────────────────▶│             │
                                            │    Error    │
                                            │             │
                                            └─────────────┘
```

**States**:
- **● (Initial)**: System starting up
- **Disconnected**: No active connection to drone
- **Connecting**: Attempting to establish MAVLink connection
- **Connected**: Active communication with drone
- **Error**: Connection error occurred

**Transitions**:
| From State | Event | To State |
|------------|-------|----------|
| Initial | System Start | Disconnected |
| Disconnected | Operator clicks "Connect" | Connecting |
| Connecting | MAVLink handshake success | Connected |
| Connecting | Connection timeout | Error |
| Connected | Communication error | Error |
| Connected | Operator clicks "Disconnect" | Disconnected |
| Connected | Connection lost/timeout | Disconnected |
| Error | Retry command | Connecting |
| Error | User cancels | Disconnected |

#### 4.3.3 Detection Processing State Machine

The Detection Processing state machine governs the bird detection workflow:

```
        ●
        │
        │ Flight Started
        ▼
┌───────────────┐
│               │ Camera Feed Lost
│     Idle      │◀──────────────────────────────-────────────┐
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Camera Feed Available                              │
        ▼                                                    │
┌───────────────┐                                            │
│               │                                            │
│   Scanning    │────────────────────────────────────────────┤
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Frame Received                                     │
        ▼                                                    │
┌───────────────┐                                            │
│               │                                            │
│  Processing   │────────────────────────────────────────────┤
│     Frame     │ Flight Stopped                             │
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Detection Result Available                         │
        ▼                                                    │
┌───────────────┐                                            │
│               │ No Birds                                   │
│     Bird      │────────────────────────────────────────────┤
│   Detected    │ Detected                                   │
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Birds Detected                                     │
        ▼                                                    │
┌───────────────┐                                            │
│               │                                            │
│    Saving     │────────────────────────────────────────────┤
│   Detection   │ Save Complete                              │
│               │                                            │
└───────────────┘                                            │
        │                                                    │
        │ Continue to Next Frame                             │
        └────────────────────────────────────────────────────┘
```

**States**:
- **● (Initial)**: Detection service starting
- **Idle**: No active detection processing
- **Scanning**: Waiting for frames to process
- **Processing Frame**: Analyzing frame with YOLO model
- **Bird Detected**: Bird found in frame, preparing to save
- **Saving Detection**: Recording detection image and data

**Transitions**:
| From State | Event | To State |
|------------|-------|----------|
| Initial | Flight Started | Idle |
| Idle | Camera Feed Available | Scanning |
| Scanning | Frame Received | Processing Frame |
| Scanning | Flight Stopped | Idle |
| Processing Frame | Detection Complete (no birds) | Scanning |
| Processing Frame | Detection Complete (birds found) | Bird Detected |
| Processing Frame | Flight Stopped | Idle |
| Bird Detected | Save detection | Saving Detection |
| Saving Detection | Save complete | Scanning |
| Scanning | Camera Feed Lost | Idle |
| Processing Frame | Camera Feed Lost | Idle |

#### 4.3.4 Chase Sequence State Machine

The Chase Sequence state machine manages bird pursuit operations:

```
        ●
        │
        │ Flight Started
        ▼
┌───────────────┐
│               │
│   Patrolling  │◀─────────────────────────────────-─────────┐
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Bird Detected                                      │
        ▼                                                    │
┌───────────────┐                                            │
│               │ Birds Out of Range                         │
│  Calculating  │────────────────────────────────────────────┤
│  Trajectory   │                                            │
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Trajectory Calculated                              │
        ▼                                                    │
┌───────────────┐                                            │
│               │                                            │
│   Pursuing    │────────────────────────────────────────────┤
│     Birds     │ Battery Low / Flight Aborted               │
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Reached Target Location                            │
        ▼                                                    │
┌───────────────┐                                            │
│               │                                            │
│   Applying    │                                            │
│    Counter    │                                            │
│   Measures    │                                            │
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        │ Counter-measure Complete                           │
        ▼                                                    │
┌───────────────┐                                            │
│               │                                            │
│  Monitoring   │                                            │
│     Birds     │                                            │
│               │                                            │
└───────┬───────┘                                            │
        │                                                    │
        ├─────────────Birds Still Present──────────────┐     │
        │                                               │    │
        │ Birds Dispersed / Lost                        │    │
        ▼                                               │    │
┌───────────────┐                                       │    │
│               │                                       │    │
│  Returning to │                                       │    │
│    Patrol     │                                       │    │
│               │                                       │    │
└───────┬───────┘                                       │    │
        │                                               │    │
        │ Back at Patrol Route                          │    │
        └───────────────────────────────────────────────┼────┘
                                                        │
                                                        │
                                                        ▼
                                                ┌───────────────┐
                                                │               │
                                                │   Pursuing    │
                                                │  (Re-engage)  │
                                                │               │
                                                └───────┬───────┘
                                                        │
                                                        │ (loops back)
                                                        └────────────────┘
```

**States**:
- **● (Initial)**: Chase system starting
- **Patrolling**: Drone following patrol route, scanning for birds
- **Calculating Trajectory**: Planning pursuit path to bird location
- **Pursuing Birds**: Moving toward detected birds
- **Applying Counter Measures**: Activating deterrents (movement/pursuit)
- **Monitoring Birds**: Observing bird response to counter-measures
- **Returning to Patrol**: Moving back to patrol route after chase

**Transitions**:
| From State | Event | To State |
|------------|-------|----------|
| Initial | Flight Started | Patrolling |
| Patrolling | Bird Detected | Calculating Trajectory |
| Calculating Trajectory | Trajectory Ready | Pursuing Birds |
| Calculating Trajectory | Birds Out of Range | Patrolling |
| Pursuing Birds | Reached Target | Applying Counter Measures |
| Pursuing Birds | Battery Low | Returning to Patrol |
| Pursuing Birds | Flight Aborted | Patrolling |
| Applying Counter Measures | Counter-measure Complete | Monitoring Birds |
| Monitoring Birds | Birds Dispersed | Returning to Patrol |
| Monitoring Birds | Birds Lost (out of view) | Returning to Patrol |
| Monitoring Birds | Birds Still Present | Pursuing Birds |
| Returning to Patrol | Back at Patrol Route | Patrolling |

---


## 5. Object-Oriented Analysis

### 5.1 Class Diagrams

```
┌─────────────────────────────────────────┐
│                AreaMap                  │
├─────────────────────────────────────────┤
│ - id: int                               │
│ - name: string                          │
│ - created_at: datetime                  │
│ - updated_at: datetime                  │
│ - boundaries: JSON                      │
│ - area_size: float                      │
│ - status: string                        │
├─────────────────────────────────────────┤
│ + create_map(): void                    │
│ + update_boundaries(boundaries): void   │
│ + validate_boundaries(): bool           │
│ + get_boundaries(): JSON                │
│ + set_status(status): void              │
│ + get_area_size(): float                │
└─────────────────────────────────────────┘
                    │
                    │ 1
                    │
                    │ *
                    ▼
┌─────────────────────────────────────────┐
│                Flight                   │
├─────────────────────────────────────────┤
│ - id: int                               │
│ - area_map_id: int (FK)                 │
│ - start_time: datetime                  │
│ - end_time: datetime                    │
│ - status: string                        │
│ - video_path: string                    │
├─────────────────────────────────────────┤
│ + start(): void                         │
│ + stop(): void                          │
│ + abort(): void                         │
│ + get_duration(): timedelta             │
│ + get_detection_count(): int            │
│ + get_detections(): List[DetectionImage]│
│ + add_detection(detection): void        │
└─────────────────────────────────────────┘
         │                    │
         │ 1                  │ 1
         │                    │
         │ 1                  │ *
         ▼                    ▼
┌─────────────────────┐  ┌─────────────────────────────────────┐
│     Telemetry       │  │          DetectionImage             │
├─────────────────────┤  ├─────────────────────────────────────┤
│ - flight_id: int    │  │ - id: int                           │
│   (PK, FK)          │  │ - flight_id: int (FK)               │
│ - battery_level:    │  │ - image_path: string                │
│   float             │  │ - timestamp: datetime               │
│ - distance: float   │  ├─────────────────────────────────────┤
│ - detections: int   │  │ + save(): void                      │
├─────────────────────┤  │ + get_flight(): Flight              │
│ + get_flight():     │  │ + get_timestamp(): datetime         │
│   Flight            │  │ + get_image_path(): string          │
│ + update_battery    │  │ + set_image_path(path): void        │
│   (level): void     │  └─────────────────────────────────────┘
│ + add_distance      │                    │
│   (dist): void      │                    │ 1
│ + increment_        │                    │
│   detections(): void│                    │ 0..1
└─────────────────────┘                    ▼
                          ┌─────────────────────────────────────┐
                          │            ChaseEvent               │
                          ├─────────────────────────────────────┤
                          │ - id: int                           │
                          │ - flight_id: int (FK)               │
                          │ - detection_image_id: int (FK)      │
                          │ - start_time: datetime              │
                          │ - end_time: datetime                │
                          │ - counter_measure_type: string      │
                          │ - outcome: string                   │
                          ├─────────────────────────────────────┤
                          │ + log_chase(): void                 │
                          │ + get_duration(): timedelta         │
                          │ + get_outcome(): string             │
                          │ + set_outcome(outcome): void        │
                          └─────────────────────────────────────┘
                                           ▲
                                           │ *
                                           │
                                           │ 1
                                     ┌─────┴─────┐
                                     │  Flight   │
                                     └───────────┘
```

**Relationship Summary:**
- AreaMap 1 ─── * Flight (One area map has many flights)
- Flight 1 ─── 1 Telemetry (One flight has one telemetry record)
- Flight 1 ─── * DetectionImage (One flight has many detection images)
- Flight 1 ─── * ChaseEvent (One flight has many chase events)
- DetectionImage 1 ─── 0..1 ChaseEvent (One detection may trigger one chase)

---

### 5.2 Class Description

#### AreaMap

**Responsibilities:**
- Stores and manages geographical boundary data for drone flight areas
- Validates boundary coordinates to ensure they form valid polygons
- Calculates total area size from boundary coordinates
- Maintains status (active/draft) for area maps

**Main methods:**

`create_map():`
```ocl
context AreaMap::create_map()
pre: name.size() > 0 and boundaries <> null
post: id > 0 and created_at = now() and updated_at = now()
```

`update_boundaries(boundaries: String):`
```ocl
context AreaMap::update_boundaries(boundaries: String)
pre: boundaries <> null and self.id > 0
post: self.boundaries = boundaries and self.updated_at = now() and self.area_size >= 0
```

`validate_boundaries(): Boolean`
```ocl
context AreaMap::validate_boundaries(): Boolean
pre: boundaries <> null
post: result = (boundaries is valid JSON and coordinate_count >= 3)
```

**Invariants:**
```ocl
context AreaMap
inv: id > 0 implies (name.size() > 0 and area_size >= 0)
inv: status = 'active' or status = 'draft'
inv: updated_at >= created_at
```

**Implementation hints:**
- Use JSON library to parse and validate boundaries format
- Boundary validation should check for minimum 3 coordinate points

---

#### Flight

**Responsibilities:**
- Manages flight session lifecycle from start to completion
- Tracks flight duration, status, and associated video recording
- Aggregates detections, telemetry, and chase events for the flight
- Enforces valid state transitions (in_progress → completed/failed/aborted)

**Main methods:**

`start():`
```ocl
context Flight::start()
pre: status <> 'in_progress'
post: status = 'in_progress' and start_time = now() and end_time = null
```

`stop():`
```ocl
context Flight::stop()
pre: status = 'in_progress'
post: status = 'completed' and end_time = now() and video_path <> null
```

`abort():`
```ocl
context Flight::abort()
pre: status = 'in_progress'
post: status = 'aborted' and end_time = now()
```

`get_duration(): TimeDelta`
```ocl
context Flight::get_duration(): TimeDelta
pre: start_time <> null
post: result = (if end_time = null then now() - start_time else end_time - start_time endif)
```

**Invariants:**
```ocl
context Flight
inv: id > 0
inv: start_time <> null
inv: end_time <> null implies end_time >= start_time
inv: status = 'in_progress' or status = 'completed' or status = 'failed' or status = 'aborted'
inv: end_time = null implies status = 'in_progress'
```

**Implementation hints:**
- start() and stop() methods should be synchronized to prevent race conditions
- get_duration() should handle case where end_time is null (flight in progress)

---

#### DetectionImage

**Responsibilities:**
- Stores reference to captured bird detection images
- Links detection events to specific flights
- Records timestamp of when detection occurred
- Maintains file path to stored detection image

**Main methods:**

`save():`
```ocl
context DetectionImage::save()
pre: flight_id > 0 and image_path.size() > 0
post: id > 0 and timestamp = now()
```

`get_timestamp(): DateTime`
```ocl
context DetectionImage::get_timestamp(): DateTime
pre: timestamp <> null
post: result = timestamp
```

**Invariants:**
```ocl
context DetectionImage
inv: id > 0
inv: flight_id > 0
inv: image_path.size() > 0
inv: timestamp <> null
```

**Implementation hints:**
- save() should trigger observer pattern to notify Flight and update telemetry
- Validate image_path points to existing file before saving

---

#### Telemetry

**Responsibilities:**
- Aggregates real-time flight metrics (battery, distance, detections)
- Maintains one-to-one relationship with Flight
- Provides methods to update individual metrics
- Acts as centralized data store for flight statistics

**Main methods:**

`update_battery(level: Float):`
```ocl
context Telemetry::update_battery(level: Float)
pre: level >= 0 and level <= 100
post: battery_level = level
```

`add_distance(dist: Float):`
```ocl
context Telemetry::add_distance(dist: Float)
pre: dist >= 0
post: distance = distance@pre + dist
```

`increment_detections():`
```ocl
context Telemetry::increment_detections()
pre: true
post: detections = detections@pre + 1
```

**Invariants:**
```ocl
context Telemetry
inv: flight_id > 0
inv: battery_level >= 0 and battery_level <= 100
inv: distance >= 0
inv: detections >= 0
```

**Implementation hints:**
- All update methods should be thread-safe for concurrent access

---

#### ChaseEvent

**Responsibilities:**
- Logs bird chase sequences with start and end times
- Records counter-measure type applied (pursuit/movement/combined)
- Tracks outcome of chase (dispersed/lost/aborted)
- Links chase event to triggering detection image (optional)

**Main methods:**

`log_chase():`
```ocl
context ChaseEvent::log_chase()
pre: flight_id > 0 and counter_measure_type <> null
post: id > 0 and start_time = now()
```

`get_duration(): TimeDelta`
```ocl
context ChaseEvent::get_duration(): TimeDelta
pre: start_time <> null
post: result = (if end_time = null then now() - start_time else end_time - start_time endif)
```

`set_outcome(outcome: String):`
```ocl
context ChaseEvent::set_outcome(outcome: String)
pre: outcome = 'dispersed' or outcome = 'lost' or outcome = 'aborted'
post: self.outcome = outcome and end_time = now()
```

**Invariants:**
```ocl
context ChaseEvent
inv: id > 0
inv: flight_id > 0
inv: start_time <> null
inv: end_time <> null implies end_time > start_time
inv: counter_measure_type = 'pursuit' or counter_measure_type = 'movement' or counter_measure_type = 'combined'
inv: outcome = null or outcome = 'dispersed' or outcome = 'lost' or outcome = 'aborted'
```

**Implementation hints:**
- counter_measure_type should be validated against enum values
- get_duration() should handle null end_time for in-progress chases

---

### 5.3 Packages

The Scarecrow Drone system is organized into a layered package hierarchy following the repository pattern and separation of concerns principle.

**Package Hierarchy:**

```
scarecrow_drone/
│
├── dto/
│   ├── area_map_dto.py
│   ├── flight_dto.py
│   ├── detection_image_dto.py
│   ├── telemetry_dto.py
│   └── chase_event_dto.py
│
├── database/
│   ├── db_connection.py
│   ├── area_map_repository.py
│   ├── flight_repository.py
│   ├── detection_image_repository.py
│   ├── telemetry_repository.py
│   └── chase_event_repository.py
│
├── services/
│   ├── area_map_service.py
│   ├── flight_service.py
│   ├── detection_service.py
│   ├── telemetry_service.py
│   ├── chase_event_service.py
│   ├── drone_service.py
│   └── recording_service.py
│
├── controllers/
│   ├── area_map_controller.py
│   ├── flight_controller.py
│   ├── detection_controller.py
│   ├── telemetry_controller.py
│   └── chase_event_controller.py
│
└── app.py
```

**Package Descriptions:**

**dto/** (Data Transfer Objects)
Contains data transfer object classes that define the structure for data exchange between layers. Each model has a corresponding DTO class:
- AreaMapDTO: Data structure for area map information
- FlightDTO: Data structure for flight session information
- DetectionImageDTO: Data structure for detection image metadata
- TelemetryDTO: Data structure for flight telemetry data
- ChaseEventDTO: Data structure for chase event records

**database/** (Data Access Layer)
Contains repository classes that handle all database operations and SQL queries. Each model has a corresponding repository:
- db_connection.py: Database connection management
- AreaMapRepository: CRUD operations for area_maps table
- FlightRepository: CRUD operations for flights table
- DetectionImageRepository: CRUD operations for detection_images table
- TelemetryRepository: CRUD operations for telemetry table
- ChaseEventRepository: CRUD operations for chase_events table

**services/** (Business Logic Layer)
Contains service classes that implement business logic and orchestrate operations between controllers and repositories:
- AreaMapService: Area mapping business logic
- FlightService: Flight management business logic
- DetectionService: Bird detection processing logic
- TelemetryService: Telemetry data processing logic
- ChaseEventService: Chase event management logic
- DroneService: Drone control and monitoring
- RecordingService: Video recording management

**controllers/** (API/Presentation Layer)
Contains controller classes that handle HTTP requests and responses, exposing REST API endpoints:
- AreaMapController: API endpoints for area map operations
- FlightController: API endpoints for flight operations
- DetectionController: API endpoints for detection data
- TelemetryController: API endpoints for telemetry data
- ChaseEventController: API endpoints for chase event data

**Package Dependencies:**

```
controllers → services → database → dto
     │           │           │
     └───────────┴───────────┴────→ (all use dto for data transfer)
```

The dependency flow follows a strict layered architecture:
1. Controllers depend on Services
2. Services depend on Repositories (database package)
3. Repositories depend on DTOs and database connection
4. All layers use DTOs for data transfer

---

### 5.4 Unit Testing

Design unit tests for each class, focusing on properties of classes and methods and their invariants. The following tests verify invariants, pre-conditions, post-conditions, and boundary conditions from Section 5.2.

#### AreaMap Unit Tests

**Invariant Tests:**
- Test inv: id > 0 implies (name.size() > 0 and area_size >= 0)
- Test inv: status = 'active' or status = 'draft'
- Test inv: updated_at >= created_at

**create_map() Tests:**
- Test pre-condition: name.size() > 0 and boundaries <> null
- Test post-condition: id > 0 and created_at = now() and updated_at = now()
- Boundary test: Empty name string (should violate pre-condition)
- Boundary test: Null boundaries (should violate pre-condition)
- Boundary test: Minimum valid boundaries with exactly 3 coordinate points

**update_boundaries() Tests:**
- Test pre-condition: boundaries <> null and self.id > 0
- Test post-condition: self.boundaries = boundaries and self.updated_at = now() and self.area_size >= 0
- Boundary test: Null boundaries (should violate pre-condition)
- Boundary test: Non-existent AreaMap with id = 0 (should violate pre-condition)
- Boundary test: Updated timestamp is greater than created timestamp

**validate_boundaries() Tests:**
- Test pre-condition: boundaries <> null
- Test post-condition: result = (boundaries is valid JSON and coordinate_count >= 3)
- Boundary test: Boundaries with less than 3 coordinate points (should return false)
- Boundary test: Invalid JSON format (should return false)
- Boundary test: Exactly 3 coordinate points (minimum valid, should return true)

---

#### Flight Unit Tests

**Invariant Tests:**
- Test inv: id > 0
- Test inv: start_time <> null
- Test inv: end_time <> null implies end_time >= start_time
- Test inv: status = 'in_progress' or status = 'completed' or status = 'failed' or status = 'aborted'
- Test inv: end_time = null implies status = 'in_progress'

**start() Tests:**
- Test pre-condition: status <> 'in_progress'
- Test post-condition: status = 'in_progress' and start_time = now() and end_time = null
- Boundary test: Calling start() when already in_progress (should violate pre-condition)
- Boundary test: Starting from 'completed' status (should succeed)
- Boundary test: Starting from 'failed' status (should succeed)

**stop() Tests:**
- Test pre-condition: status = 'in_progress'
- Test post-condition: status = 'completed' and end_time = now() and video_path <> null
- Boundary test: Calling stop() when not in_progress (should violate pre-condition)
- Boundary test: End time is after start time
- Boundary test: Video path is set after stopping

**abort() Tests:**
- Test pre-condition: status = 'in_progress'
- Test post-condition: status = 'aborted' and end_time = now()
- Boundary test: Calling abort() when not in_progress (should violate pre-condition)
- Boundary test: End time is after start time

**get_duration() Tests:**
- Test pre-condition: start_time <> null
- Test post-condition: result = (if end_time = null then now() - start_time else end_time - start_time endif)
- Boundary test: Duration when flight is in progress (end_time = null)
- Boundary test: Duration when flight is completed (end_time set)
- Boundary test: Duration is always non-negative

---

#### DetectionImage Unit Tests

**Invariant Tests:**
- Test inv: id > 0
- Test inv: flight_id > 0
- Test inv: image_path.size() > 0
- Test inv: timestamp <> null

**save() Tests:**
- Test pre-condition: flight_id > 0 and image_path.size() > 0
- Test post-condition: id > 0 and timestamp = now()
- Boundary test: flight_id = 0 (should violate pre-condition)
- Boundary test: Empty image_path (should violate pre-condition)
- Boundary test: Non-existent flight_id (should violate pre-condition)
- Boundary test: Timestamp is automatically set on save

**get_timestamp() Tests:**
- Test pre-condition: timestamp <> null
- Test post-condition: result = timestamp
- Boundary test: Accessing timestamp before save (should handle gracefully)
- Boundary test: Timestamp remains unchanged after retrieval

---

#### Telemetry Unit Tests

**Invariant Tests:**
- Test inv: flight_id > 0
- Test inv: battery_level >= 0 and battery_level <= 100
- Test inv: distance >= 0
- Test inv: detections >= 0

**update_battery() Tests:**
- Test pre-condition: level >= 0 and level <= 100
- Test post-condition: battery_level = level
- Boundary test: level = 0 (minimum valid value)
- Boundary test: level = 100 (maximum valid value)
- Boundary test: level = -1 (should violate pre-condition)
- Boundary test: level = 101 (should violate pre-condition)
- Boundary test: level = 50.5 (valid decimal value)

**add_distance() Tests:**
- Test pre-condition: dist >= 0
- Test post-condition: distance = distance@pre + dist
- Boundary test: dist = 0 (should succeed, no change)
- Boundary test: dist < 0 (should violate pre-condition)
- Boundary test: Adding distance multiple times accumulates correctly
- Boundary test: Large distance values

**increment_detections() Tests:**
- Test pre-condition: true
- Test post-condition: detections = detections@pre + 1
- Boundary test: Starting from detections = 0
- Boundary test: Incrementing multiple times
- Boundary test: Detections count never decreases

---

#### ChaseEvent Unit Tests

**Invariant Tests:**
- Test inv: id > 0
- Test inv: flight_id > 0
- Test inv: start_time <> null
- Test inv: end_time <> null implies end_time > start_time
- Test inv: counter_measure_type = 'pursuit' or counter_measure_type = 'movement' or counter_measure_type = 'combined'
- Test inv: outcome = null or outcome = 'dispersed' or outcome = 'lost' or outcome = 'aborted'

**log_chase() Tests:**
- Test pre-condition: flight_id > 0 and counter_measure_type <> null
- Test post-condition: id > 0 and start_time = now()
- Boundary test: flight_id = 0 (should violate pre-condition)
- Boundary test: Null counter_measure_type (should violate pre-condition)
- Boundary test: Invalid counter_measure_type value (should violate invariant)

**get_duration() Tests:**
- Test pre-condition: start_time <> null
- Test post-condition: result = (if end_time = null then now() - start_time else end_time - start_time endif)
- Boundary test: Duration when chase is in progress (end_time = null)
- Boundary test: Duration when chase is ended (end_time set)
- Boundary test: Duration is always non-negative

**set_outcome() Tests:**
- Test pre-condition: outcome = 'dispersed' or outcome = 'lost' or outcome = 'aborted'
- Test post-condition: self.outcome = outcome and end_time = now()
- Boundary test: Invalid outcome value (should violate pre-condition)
- Boundary test: Setting outcome 'dispersed' (valid)
- Boundary test: Setting outcome 'lost' (valid)
- Boundary test: Setting outcome 'aborted' (valid)
- Boundary test: End time is set when outcome is set
- Boundary test: End time is after start time

---


## 6. User Interface Draft

Describe the main user interfaces of the system. Simple drawings of the main screens focusing on inputs and outputs.

### 6.1 Area Mapping Interface

**Purpose:** Create and manage area maps with defined boundaries for flight operations.

**Inputs:**
- Area name (text)
- Boundary coordinates (map interface or JSON)
- Status selection (active/draft)

**Outputs:**
- Area map ID
- Calculated area size
- Visual boundary display
- Validation status

**Interface:**

+-----------------------------------------------------------------------+
|  Area Mapping                                       [Dashboard] [Help] |
+-----------------------------------------------------------------------+
|                                                                       |
|  Area Name: [_____________________]                                  |
|                                                                       |
|  Status: ( ) Active  (X) Draft                                       |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Boundary Definition                                            |  |
|  |                                                                |  |
|  |  Option 1: Upload JSON                                         |  |
|  |  [Choose File] boundaries.json                                 |  |
|  |                                                                |  |
|  |  Option 2: Draw on Map                                         |  |
|  |  +----------------------------------------------------------+  |  |
|  |  |                                                          |  |  |
|  |  |           [Map View with Drawing Tools]                 |  |  |
|  |  |                                                          |  |  |
|  |  |  Tools: [Point] [Polygon] [Clear]                       |  |  |
|  |  |                                                          |  |  |
|  |  +----------------------------------------------------------+  |  |
|  |                                                                |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  Calculated Area Size: 1250.5 sq meters                              |
|  Coordinate Count: 8 points                                          |
|  Validation: [Valid polygon]                                         |
|                                                                       |
|  [Save Area Map]  [Validate Boundaries]  [Cancel]                    |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Existing Area Maps                                             |  |
|  |----------------------------------------------------------------|  |
|  | ID | Name          | Size (sq m) | Status | Created           |  |
|  |----|---------------|-------------|--------|-------------------|  |
|  | 1  | North Field   | 1250.5      | Active | 2026-01-15 10:30  |  |
|  | 2  | South Garden  | 890.2       | Draft  | 2026-01-16 14:20  |  |
|  | 3  | East Pasture  | 2100.0      | Active | 2026-01-17 09:15  |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+

---

### 6.2 Flight Control Dashboard

**Purpose:** Start, monitor, and stop flight operations.

**Inputs:**
- Area map selection (dropdown)
- Start/Stop flight buttons
- Abort mission button

**Outputs:**
- Flight status
- Current flight ID
- Live video feed
- Real-time telemetry data

**Interface:**

+-----------------------------------------------------------------------+
|  Flight Control Dashboard                      [Status: Ready]        |
+-----------------------------------------------------------------------+
|                                                                       |
|  Select Area Map: [North Field v]                                    |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  |                       Live Camera Feed                         |  |
|  |                                                                |  |
|  |                    +----------------------+                    |  |
|  |                    |                      |                    |  |
|  |                    |   [Video Stream]     |                    |  |
|  |                    |                      |                    |  |
|  |                    +----------------------+                    |  |
|  |                                                                |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  +-------------------------+  +-------------------------+             |
|  |   [START FLIGHT]        |  |   [STOP FLIGHT]         |             |
|  +-------------------------+  +-------------------------+             |
|                                                                       |
|  +-------------------------+                                          |
|  |   [ABORT MISSION]       |                                          |
|  +-------------------------+                                          |
|                                                                       |
|  Current Flight: Flight ID #12                                       |
|  Status: In Progress                                                 |
|                                                                       |
|  [View Flight History]  [View Telemetry]  [View Detections]          |
|                                                                       |
+-----------------------------------------------------------------------+

---

### 6.3 Flight Telemetry View

**Purpose:** Display real-time telemetry data during flight operations.

**Inputs:**
- Flight ID (auto-selected from active flight)

**Outputs:**
- Battery level
- Distance traveled
- Detection count
- Timestamp of last update

**Interface:**

+-----------------------------------------------------------------------+
|  Flight Telemetry - Flight #12                     [Refresh] [Back]   |
+-----------------------------------------------------------------------+
|                                                                       |
|  Flight Details:                                                     |
|  Start Time: 14:30:22                                                |
|  Duration: 00:05:32                                                  |
|  Status: In Progress                                                 |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Real-time Metrics                                              |  |
|  |----------------------------------------------------------------|  |
|  |                                                                |  |
|  |  Battery Level:  [=========>          ] 65%                   |  |
|  |                                                                |  |
|  |  Distance Traveled:  245.8 meters                             |  |
|  |                                                                |  |
|  |  Total Detections:  12 birds                                  |  |
|  |                                                                |  |
|  |  Last Updated:  14:35:54                                      |  |
|  |                                                                |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Telemetry History (Last 10 updates)                           |  |
|  |----------------------------------------------------------------|  |
|  | Time     | Battery | Distance | Detections                      |  |
|  |----------|---------|----------|--------------------------------|  |
|  | 14:35:54 | 65%     | 245.8 m  | 12                             |  |
|  | 14:35:24 | 67%     | 230.2 m  | 10                             |  |
|  | 14:34:54 | 70%     | 210.5 m  | 8                              |  |
|  | 14:34:24 | 72%     | 190.1 m  | 7                              |  |
|  | 14:33:54 | 75%     | 165.3 m  | 5                              |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+

---

### 6.4 Detection Image Gallery

**Purpose:** View detection images captured during a flight.

**Inputs:**
- Flight ID (from flight history)
- Image filters (optional)

**Outputs:**
- Grid of detection images
- Image metadata (timestamp, path)
- Detection count per image

**Interface:**

+-----------------------------------------------------------------------+
|  Detection Images - Flight #5                      [Back to History]  |
+-----------------------------------------------------------------------+
|                                                                       |
|  Flight: 2026-01-18 14:30 - 14:45 | Duration: 15 min | 23 detections  |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Detection Image Gallery                                        |  |
|  |                                                                |  |
|  |  +--------------+  +--------------+  +--------------+          |  |
|  |  |              |  |              |  |              |          |  |
|  |  | [Image 1]    |  | [Image 2]    |  | [Image 3]    |          |  |
|  |  |              |  |              |  |              |          |  |
|  |  | 14:31:22     |  | 14:33:45     |  | 14:35:12     |          |  |
|  |  | ID: 101      |  | ID: 102      |  | ID: 103      |          |  |
|  |  +--------------+  +--------------+  +--------------+          |  |
|  |                                                                |  |
|  |  +--------------+  +--------------+  +--------------+          |  |
|  |  |              |  |              |  |              |          |  |
|  |  | [Image 4]    |  | [Image 5]    |  | [Image 6]    |          |  |
|  |  |              |  |              |  |              |          |  |
|  |  | 14:36:58     |  | 14:38:03     |  | 14:40:27     |          |  |
|  |  | ID: 104      |  | ID: 105      |  | ID: 106      |          |  |
|  |  +--------------+  +--------------+  +--------------+          |  |
|  |                                                                |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  [Download All Images]  [View Flight Video]                          |
|                                                                       |
+-----------------------------------------------------------------------+

---

### 6.5 Chase Event Log

**Purpose:** View and manage chase event records for a flight.

**Inputs:**
- Flight ID (from flight history)
- Event filters (counter measure type, outcome)

**Outputs:**
- List of chase events
- Event details (start/end time, duration, outcome)
- Counter measure type used

**Interface:**

+-----------------------------------------------------------------------+
|  Chase Events - Flight #5                          [Back to History]  |
+-----------------------------------------------------------------------+
|                                                                       |
|  Flight: 2026-01-18 14:30 - 14:45 | Total Chase Events: 8             |
|                                                                       |
|  Filters: Counter Measure [All v]  Outcome [All v]  [Apply]          |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Chase Event Log                                                |  |
|  |----------------------------------------------------------------|  |
|  | ID | Start    | End      | Duration | Counter Measure | Outcome|  |
|  |----|----------|----------|----------|-----------------|--------|  |
|  | 1  | 14:31:25 | 14:31:58 | 00:00:33 | Pursuit         |Dispersed|  |
|  | 2  | 14:33:10 | 14:33:45 | 00:00:35 | Movement        |Dispersed|  |
|  | 3  | 14:35:20 | 14:36:10 | 00:00:50 | Combined        |Dispersed|  |
|  | 4  | 14:37:05 | 14:37:30 | 00:00:25 | Pursuit         | Lost    |  |
|  | 5  | 14:38:15 | 14:39:00 | 00:00:45 | Movement        |Dispersed|  |
|  | 6  | 14:40:10 | 14:40:50 | 00:00:40 | Combined        |Dispersed|  |
|  | 7  | 14:42:00 | 14:42:20 | 00:00:20 | Pursuit         |Aborted  |  |
|  | 8  | 14:43:30 | 14:44:15 | 00:00:45 | Movement        |Dispersed|  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Event Details - Chase Event #3                                 |  |
|  |----------------------------------------------------------------|  |
|  |  Start Time: 14:35:20                                          |  |
|  |  End Time: 14:36:10                                            |  |
|  |  Duration: 50 seconds                                          |  |
|  |  Counter Measure: Combined (Pursuit + Movement)                |  |
|  |  Outcome: Dispersed                                            |  |
|  |  Detection Image ID: 103                                       |  |
|  |                                                                |  |
|  |  [View Detection Image]                                        |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  Summary:                                                            |
|  Total Events: 8 | Dispersed: 6 | Lost: 1 | Aborted: 1               |
|  Avg Duration: 38 seconds                                            |
|                                                                       |
+-----------------------------------------------------------------------+

---

### 6.6 Flight History

**Purpose:** View historical flight records and access detailed flight information.

**Inputs:**
- Date range filter
- Status filter
- Search query

**Outputs:**
- List of flights with metadata
- Flight summary statistics
- Navigation to detail views

**Interface:**

+-----------------------------------------------------------------------+
|  Flight History                                     [Back to Dashboard]|
+-----------------------------------------------------------------------+
|                                                                       |
|  Filters:                                                             |
|  Date Range: [2026-01-01 v] to [2026-01-31 v]                        |
|  Status: [All v]  Search: [____________]  [Apply Filters]            |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Flight Records                                                 |  |
|  |----------------------------------------------------------------|  |
|  | ID | Start Time      | End Time        | Status     | Detect. |  |
|  |----|-----------------|-----------------|------------|---------|  |
|  | 5  | 2026-01-18 14:30| 2026-01-18 14:45| Completed  | 23      |  |
|  |    | [View] [Telemetry] [Detections] [Chase Events]            |  |
|  |----|-----------------|-----------------|------------|---------|  |
|  | 4  | 2026-01-18 10:15| 2026-01-18 10:28| Completed  | 8       |  |
|  |    | [View] [Telemetry] [Detections] [Chase Events]            |  |
|  |----|-----------------|-----------------|------------|---------|  |
|  | 3  | 2026-01-17 16:00| 2026-01-17 16:22| Completed  | 15      |  |
|  |    | [View] [Telemetry] [Detections] [Chase Events]            |  |
|  |----|-----------------|-----------------|------------|---------|  |
|  | 2  | 2026-01-17 09:45| 2026-01-17 09:52| Failed     | 0       |  |
|  |    | [View] [Telemetry] [Detections] [Chase Events]            |  |
|  |----|-----------------|-----------------|------------|---------|  |
|  | 1  | 2026-01-16 11:30| 2026-01-16 11:55| Completed  | 31      |  |
|  |    | [View] [Telemetry] [Detections] [Chase Events]            |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  [<< Previous]          Page 1 of 3          [Next >>]               |
|                                                                       |
+-----------------------------------------------------------------------+

---

## 7. Testing

### 7.1 Test Strategy

| Category | Description | Tools |
|----------|-------------|-------|
| Unit Tests | Tests for individual components in isolation | pytest, pytest-asyncio |
| Integration Tests | Tests for component interactions and API endpoints | pytest, TestClient |

### 7.2 Unit Tests

#### 7.2.1 Entity Tests

| ID | Component | Test Focus | Key Validations |
|----|-----------|------------|-----------------|
| UT-01 | Flight | Lifecycle management | State transitions (start→stop→abort), duration calculation, timestamp integrity |
| UT-02 | AreaMap | Boundary validation | Valid coordinates, minimum 3 points, area calculation |
| UT-03 | DetectionImage | Image storage | Valid flight reference, path validation, timestamp |
| UT-04 | Telemetry | Data constraints | Battery 0-100%, non-negative distance/detections |
| UT-05 | ChaseEvent | Chase lifecycle | Valid counter-measure types, outcome states |

#### 7.2.2 Repository Tests

| ID | Component | Test Focus | Key Validations |
|----|-----------|------------|-----------------|
| UT-06 | FlightRepository | CRUD operations | Create/read/update/delete flights, status mapping |
| UT-07 | DroneRepository | Flight & telemetry storage | Active flight tracking, telemetry save/retrieve, detection images |
| UT-08 | AreaMapRepository | Area map persistence | Boundary storage, active map filtering |
| UT-09 | TelemetryRepository | Telemetry persistence | Save/retrieve telemetry records, flight association |

#### 7.2.3 Service Tests

| ID | Component | Test Focus | Key Validations |
|----|-----------|------------|-----------------|
| UT-10 | ConnectionService | Connection management | WiFi detection, SSH connect/disconnect, mock mode |
| UT-11 | DroneService | Flight orchestration | Start/stop flight, detection integration, error handling |
| UT-12 | FlightService | Flight data access | History retrieval, summary calculation, data formatting |
| UT-13 | DetectionService | Detection process | Process lifecycle, output parsing, image saving |
| UT-14 | RecordingService | Video recording | GStreamer process management, file creation |
| UT-15 | AreaMapService | Area mapping logic | Boundary validation, mapping flight initiation, area storage |
| UT-16 | ChaseService | Chase orchestration | Pursuit trajectory, counter-measure activation, chase logging |

#### 7.2.4 Controller Tests

| ID | Component | Test Focus | Key Validations |
|----|-----------|------------|-----------------|
| UT-17 | ConnectionController | Connection endpoints | WiFi/SSH status, connect/disconnect responses |
| UT-18 | DroneController | Drone control endpoints | Start/stop/abort responses, status reporting |
| UT-19 | FlightController | Flight data endpoints | History list, flight details, 404 handling |
| UT-20 | AreaMapController | Area map endpoints | CRUD operations, mapping status responses |

#### 7.2.5 Detection System Tests

| ID | Component | Test Focus | Key Validations |
|----|-----------|------------|-----------------|
| UT-21 | PigeonDetector | ML detection | Model loading, frame processing, detection output |

### 7.3 Integration Tests

| ID | Test Focus | Key Validations |
|----|------------|-----------------|
| IT-01 | API Endpoints | All REST endpoints return correct status codes and responses |
| IT-02 | Flight Flow | Complete flight cycle (connect → start → detect → stop) works correctly |
| IT-03 | Database Operations | Flight lifecycle persists correctly across services |
| IT-04 | WebSocket Communication | Telemetry broadcasts to all connected frontends |
| IT-05 | Service Coordination | DroneService correctly orchestrates Connection, Detection, and Recording services |

---

## Appendix A: API Endpoints

### A.1 Connection Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | /api/connection/wifi | Check WiFi connection to drone | - | `{ connected: boolean, ssid?: string }` |
| POST | /api/connection/ssh | Establish SSH connection to drone | - | `{ success: boolean, error?: string }` |
| DELETE | /api/connection/ssh | Disconnect SSH from drone | - | `{ success: boolean }` |
| GET | /api/connection/status | Get full connection status | - | `{ wifiConnected: boolean, sshConnected: boolean, droneReady: boolean, streamActive: boolean }` |
| POST | /api/connection/video/start | Start video stream from drone | - | `{ success: boolean, streamUrl?: string }` |
| POST | /api/connection/video/stop | Stop video stream | - | `{ success: boolean }` |

### A.2 Drone Control Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | /api/drone/status | Get drone operational status | - | `{ isConnected: boolean, isFlying: boolean, mode: string, batteryLevel?: number }` |
| POST | /api/drone/start | Start flight mission | `{ areaMapId?: number }` | `{ success: boolean, flightId: string, error?: string }` |
| POST | /api/drone/stop | Stop flight mission gracefully | - | `{ success: boolean, pigeonsDetected: number, framesProcessed: number }` |
| POST | /api/drone/abort | Emergency abort mission | - | `{ success: boolean, pigeonsDetected: number, framesProcessed: number }` |
| POST | /api/drone/return-home | Command drone to return to home | - | `{ success: boolean }` |
| GET | /api/drone/telemetry | Get current telemetry data | - | `{ mode: string, armed: boolean, location: Location, attitude: Attitude, groundspeed: number }` |
| WS | /api/drone/telemetry/stream | WebSocket for real-time telemetry | - | Continuous telemetry updates |

### A.3 Flight History Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | /api/flights | Get all flight records | - | `Flight[]` |
| GET | /api/flights/{id} | Get flight by ID | - | `Flight` |
| GET | /api/flights/{id}/summary | Get flight summary statistics | - | `{ flightId: string, duration: number, avgSpeed: number, totalDetections: number }` |
| GET | /api/flights/{id}/images | Get detection images for flight | - | `{ images: string[] }` |
| GET | /api/flights/{id}/recording | Get video recording path | - | `{ recording: string \| null }` |
| GET | /api/flights/{id}/telemetry | Get telemetry history for flight | - | `Telemetry[]` |
| DELETE | /api/flights/{id} | Delete flight record | - | `{ success: boolean }` |

### A.4 Area Map Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | /api/areas | Get all area maps | - | `AreaMap[]` |
| GET | /api/areas/{id} | Get area map by ID | - | `AreaMap` |
| POST | /api/areas | Create new area map | `{ name: string, boundaries: Coordinate[], homePoint: Coordinate }` | `{ success: boolean, areaId: number }` |
| PUT | /api/areas/{id} | Update area map | `{ name?: string, boundaries?: Coordinate[], homePoint?: Coordinate }` | `{ success: boolean }` |
| DELETE | /api/areas/{id} | Delete area map | - | `{ success: boolean }` |
| GET | /api/areas/{id}/flights | Get flights for area map | - | `Flight[]` |
| POST | /api/areas/mapping/start | Start area mapping flight | `{ name: string }` | `{ success: boolean, mappingId: number }` |
| GET | /api/areas/mapping/status | Get mapping flight status | - | `{ active: boolean, progress?: number, boundaries?: Coordinate[] }` |

### A.5 Detection Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | /api/detection/status | Get detection service status | - | `{ running: boolean, flightId?: number, detectionCount: number }` |
| GET | /api/detection/config | Get detection configuration | - | `{ confidenceThreshold: number, modelPath: string }` |
| PUT | /api/detection/config | Update detection configuration | `{ confidenceThreshold?: number }` | `{ success: boolean }` |

### A.6 Chase Event Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | /api/flights/{id}/chases | Get chase events for flight | - | `ChaseEvent[]` |
| GET | /api/chases/{id} | Get chase event details | - | `ChaseEvent` |

---

## Appendix B: File Structure

```
scarecrow_drone/
├── scarecrow-drone/                    # Main application
│   ├── backend/
│   │   ├── app.py                      # FastAPI application entry point
│   │   ├── controllers/                # API route handlers
│   │   ├── services/                   # Business logic layer
│   │   ├── database/                   # Data access layer (repositories)
│   │   ├── dto/                        # Data transfer objects
│   │   └── models/                     # Entity models
│   ├── database/
│   │   ├── database.py                 # Database schema initialization
│   │   └── scarecrow.db                # SQLite database file
│   └── frontend/
│       ├── public/                     # Static assets
│       ├── src/
│       │   ├── pages/                  # Page components
│       │   ├── components/             # Reusable UI components
│       │   ├── services/               # API client
│       │   ├── types/                  # TypeScript definitions
│       │   └── hooks/                  # Custom React hooks
│       └── package.json
├── live_detection/                     # Detection module
│   ├── pigeon_detector.py              # PigeonDetector class
│   ├── best_v4.pt                      # YOLOv8 trained model
│   └── recordings/                     # Detection video recordings
├── pigeon-detection/                   # ML Training module
│   ├── src/                            # Training scripts
│   ├── data/                           # Training datasets (train/valid/test)
│   ├── models/                         # Saved model weights
│   └── runs/                           # Training run outputs
├── drone_scripts/                      # Drone control scripts
├── tests/                              # Test suite
│   ├── backend/unit/                   # Unit tests
│   ├── backend/integration/            # Integration tests
│   └── detection/                      # Detection tests
├── recordings/                         # Flight video recordings
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```
