# Scarecrow Drone

Web-based control interface for Intel Aero RTF drone with pigeon detection capabilities.

## Current Status (December 2024)

### What Works
- SSH connection to drone at `192.168.1.1` (Intel Aero WiFi AP mode)
- Web frontend (React) and backend (FastAPI) running locally
- Flight scripts uploaded to drone at `/home/root/drone_scripts/`
- EKF/GPS parameters configured for indoor flight (no GPS required)

### Current Issue: GPS Preflight Check
**Problem**: `PREFLIGHT FAIL: GPS RECEIVER MISSING` blocks arming even with GPS disabled in EKF.

**Solution Found**: Set `CBRK_GPSFAIL = 240024` (circuit breaker to disable GPS fail check)

**Status**: Parameter is set and saved, but **requires drone reboot** to take effect.

### Next Steps
1. **Reboot the drone** (power cycle)
2. Run `python start_flight.py` on the drone
3. Verify arming succeeds without GPS

---

## Architecture

```
Windows PC (192.168.1.2)              Intel Aero Drone (192.168.1.1)
┌─────────────────────────┐           ┌─────────────────────────────┐
│  Frontend (React:3000)  │           │  Yocto Linux (Python 2.7)   │
│  Backend (FastAPI:5000) │◄──SSH────►│  /home/root/drone_scripts/  │
│                         │           │  PX4 Flight Controller      │
└─────────────────────────┘           │  /dev/ttyS1 @ 1500000 baud  │
                                      └─────────────────────────────┘
```

## Project Structure

```
scarecrow-drone/
├── frontend/                  # React TypeScript app
│   ├── src/
│   │   ├── components/
│   │   │   ├── DroneControl.tsx
│   │   │   └── FlightHistory.tsx
│   │   └── services/api.ts
│   └── package.json
│
├── backend/                   # FastAPI Python backend
│   ├── app.py                 # Main API routes
│   ├── services/
│   │   ├── connection_service.py  # SSH to drone
│   │   └── drone_service.py       # Flight operations
│   ├── repositories/
│   │   └── drone_repository.py    # SQLite DB
│   └── venv/                  # Python virtual env
│
├── drone_scripts/             # Scripts that run ON THE DRONE
│   ├── start_flight.py        # Main flight: arm, takeoff, hover, land
│   ├── start_flight_v2.py     # Alternative version (waits for EKF)
│   ├── check_ekf_params.py    # Check/set EKF parameters
│   ├── altitude_monitor.py    # DroneKit altitude test
│   └── mavlink_altitude_test.py # pymavlink altitude test
│
└── README.md
```

## Drone Connection Details

| Setting | Value |
|---------|-------|
| Drone IP | `192.168.1.1` |
| SSH User | `root` |
| SSH Key | `~/.ssh/id_rsa_drone` |
| SSH Options | `-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa` |
| Serial Port | `/dev/ttyS1` |
| Baud Rate | `1500000` |
| Python Version | `2.7` (Yocto factory image) |

## Flight Script Parameters (No GPS Indoor Flight)

The `start_flight.py` script configures these parameters for GPS-less operation:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `EKF2_AID_MASK` | 0 | Don't require GPS sensor fusion |
| `EKF2_HGT_MODE` | 0 | Use barometer for height estimation |
| `COM_ARM_WO_GPS` | 1 | Allow arming without GPS fix |
| `EKF2_GPS_CHECK` | 0 | Disable GPS quality checks |
| `CBRK_GPSFAIL` | 240024 | **Circuit breaker: disable GPS fail check** |

**Important**: `CBRK_GPSFAIL` requires a reboot to take effect!

## Flight Script Features

### start_flight.py
- **Safety**: 10-second watchdog auto-kills motors
- **Emergency Stop**: Ctrl+C immediately disarms
- **RC Override**: Uses channel 3 (throttle) PWM control
- **Throttle Values**:
  - Takeoff: 1160 PWM
  - Hover: 1210 PWM
  - Land: 1090 PWM
  - Min: 1000 PWM

### Flight Sequence
1. Connect to flight controller
2. Configure EKF parameters (no GPS)
3. Force arm (MAV_CMD 400 with param2=21196)
4. Ramp throttle to takeoff
5. Hover for 3 seconds
6. Gradual descent to land
7. Disarm motors

## Running the Project

### Start Backend
```bash
cd backend
./venv/Scripts/python.exe -m uvicorn app:app --reload --port 5000
```

### Start Frontend
```bash
cd frontend
npm start
```

### Upload Script to Drone
```bash
cat drone_scripts/start_flight.py | ssh -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedKeyTypes=+ssh-rsa -i ~/.ssh/id_rsa_drone \
  root@192.168.1.1 "cat > /home/root/drone_scripts/start_flight.py"
```

### Run Flight Script
```bash
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa \
  -i ~/.ssh/id_rsa_drone root@192.168.1.1 \
  "cd /home/root/drone_scripts && python start_flight.py"
```

## Troubleshooting

### "PREFLIGHT FAIL: GPS RECEIVER MISSING"
The GPS circuit breaker is blocking arm. Solution:
1. Verify `CBRK_GPSFAIL = 240024` is set
2. **Reboot the drone** (power cycle)
3. Try arming again

### EKF Not Converging
Without GPS, EKF may not report `ekf_ok=True`. The script now **skips EKF check** and uses force arm.

### SSH Connection Refused
- Check drone WiFi is connected (SSID: intel-aero-XXXX)
- Drone might be at `192.168.8.1` instead of `192.168.1.1`
- Wait 30+ seconds after boot for WiFi to start

### Serial Port Busy
Another process may hold `/dev/ttyS1`. Kill mavlink_bridge:
```bash
ssh root@192.168.1.1 "fuser -k /dev/ttyS1"
```

## Key Files Reference

| File | Location | Purpose |
|------|----------|---------|
| `start_flight.py` | drone:/home/root/drone_scripts/ | Main indoor flight script |
| `connection_service.py` | backend/services/ | SSH communication |
| `drone_service.py` | backend/services/ | Flight orchestration |
| `DroneControl.tsx` | frontend/src/components/ | UI controls |

## MAVLink Commands Used

| Command | ID | Purpose |
|---------|-----|---------|
| `MAV_CMD_COMPONENT_ARM_DISARM` | 400 | Arm/disarm motors |
| Force flag | param2=21196 | Bypass pre-arm checks |
| RC Override | Channel 3 | Throttle control (1000-2000 PWM) |

## Development Notes

- Drone runs Python 2.7 - use `print "text"` syntax in drone scripts
- DroneKit `wait_ready=False` is required (no GPS = never ready)
- Parameters set via MAVLink may need reboot to take effect
- Always test with props removed first!
