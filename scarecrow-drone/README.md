# Scarecrow Drone

Web-based control interface and telemetry database for Intel Aero pigeon detection drone.

## Overview

React frontend with military/metallic theme for drone control and flight history management. SQLite backend for storing flight telemetry data.

## Structure

```
scarecrow-drone/
├── frontend/              # React TypeScript app
│   ├── src/
│   │   ├── components/
│   │   │   ├── DroneControl.tsx
│   │   │   └── FlightHistory.tsx
│   │   ├── pages/
│   │   │   └── Dashboard.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── flight.ts
│   └── package.json
├── backend/
│   └── database.py        # SQLite database
└── tests/                 # Drone test scripts
    ├── drone_info.py
    ├── simple_flight_mission.py
    ├── take_picture.py
    └── record_video.py
```

## Features

- Start/Stop flight control
- Real-time drone status display
- Flight history with telemetry records
- Military/metallic themed UI

## Database Schema

### Flights Table
- flight_id (PRIMARY KEY)
- start_time
- end_time
- status
- notes

### Telemetry Table
Recorded every second during flight:
- mode
- armed
- battery
- gps
- location
- attitude
- groundspeed

## Installation

### Frontend

```bash
cd frontend
npm install
npm start
```

### Backend

```bash
pip install flask flask-cors
python backend/database.py  # Initialize database
```

## Usage

1. Start the backend API
2. Start the React frontend
3. Open http://localhost:3000

## Requirements

### Frontend
- Node.js 16+
- React 18
- TypeScript

### Backend
- Python 3.8+
- SQLite3
- DroneKit (for drone communication)
