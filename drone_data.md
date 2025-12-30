# Drone System Documentation

## Hardware & System Information

### Drone Model
- **Model**: Intel Aero Ready to Fly (RTF)
- **IP Address**: 192.168.1.1
- **Operating System**: Yocto Linux
- **Default User**: root (no password required)

### Flight Controller Connection
- **Port**: `/dev/ttyS1`
- **Baud Rate**: 1500000
- **Protocol**: MAVLink
- **Heartbeat Timeout**: 30 seconds
- **Source System ID**: 255

### Connection String (DroneKit)
```python
vehicle = connect('/dev/ttyS1',
                 wait_ready=False,
                 baud=1500000,
                 heartbeat_timeout=30,
                 source_system=255)
```

## Altitude Evaluation Methods

### 1. DroneKit Built-in Properties
DroneKit provides direct access to altitude through the vehicle object:

```python
# Relative altitude (from home/takeoff point)
vehicle.location.global_relative_frame.alt

# Absolute altitude (mean sea level)
vehicle.location.global_frame.alt

# Rangefinder distance (if equipped)
vehicle.rangefinder.distance
```

**Note**: Requires `wait_ready=True` or manual wait for location data to be available.

### 2. MAVLink Message Sources

Multiple MAVLink messages provide altitude data:

| Message Type | Field | Description |
|--------------|-------|-------------|
| `LOCAL_POSITION_NED` | `-msg.z` | Local position in NED frame (best for indoor/no GPS) |
| `GLOBAL_POSITION_INT` | `msg.relative_alt / 1000.0` | GPS-based relative altitude (mm to meters) |
| `ALTITUDE` | `msg.altitude_relative` | Dedicated altitude message |
| `VFR_HUD` | `msg.alt` | Basic telemetry altitude |

### 3. Custom Altitude Filter

The custom `AltitudeFilter` class implements a **hybrid complementary filter** to stabilize altitude estimates:

#### Key Features:
- **Home Reference**: Sets initial altitude as home (0m reference point)
- **Stationary Detection**: Uses IMU accelerometer (total accel ≈ 9.8 m/s² = gravity only)
- **Drift Correction**: When stationary for 3+ readings, gently corrects drift
- **Velocity Integration**: During movement, combines velocity integration (80%) with raw readings (10%)
- **Smooth Filtering**: Reduces sensor noise and handles rapid fluctuations

#### Data Sources:
- **Raw Altitude**: `LOCAL_POSITION_NED` message (`-msg.z`)
- **IMU Data**: `SCALED_IMU2`, `SCALED_IMU`, or `RAW_IMU` messages
  - Converted from millig to m/s²: `msg.xacc / 1000.0 * 9.8`

#### Algorithm:
```
When Stationary:
  altitude = altitude * 0.95 + relative_alt * 0.05
  velocity = 0

When Moving:
  velocity = velocity * 0.8 + raw_velocity * 0.2
  altitude += velocity * dt
  altitude = altitude * 0.9 + relative_alt * 0.1
```

## Common Issues & Solutions

### 1. Multiple Access on Port Error
**Error**: `device reports readiness to read but returned no data (device disconnected or multiple access on port?)`

**Cause**: The `mavlink_bridge.py` process is already connected to `/dev/ttyS1`

**Solution**:
```bash
# Find the process
ps | grep python

# Kill mavlink_bridge
kill <PID>
# or
killall python2
```

**Process to look for**:
```
root 203m S python2 /usr/sbin/mavlink_bridge.py 192.168.1.2
```

### 2. Invalid MAVLink Prefix Error
**Error**: `invalid MAVLink prefix '32'`

**Cause**: Corrupt MAVLink messages in buffer or bad connection state

**Solutions**:
- Add message buffer clearing on initialization (flush for 1-2 seconds)
- Use blocking reads with timeout instead of non-blocking: `recv_match(blocking=True, timeout=0.5)`
- Wait longer after connection (2+ seconds)
- Try multiple message types as fallback

### 3. Null/Missing Altitude Data
**Cause**: Drone not armed, GPS not ready, or wrong message type

**Solutions**:
- Try multiple altitude message sources (see MAVLink table above)
- Ensure drone is armed or sensors are initialized
- Use `wait_ready=True` in DroneKit connect
- Initialize altitude filter with multiple readings (5-10 samples)

## SSH & File Transfer

### SSH Connection
```bash
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@192.168.1.1
```

### SCP File Transfer (from Windows)
```powershell
scp -O -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa "C:\path\to\file.py" root@192.168.1.1:~/
```

### Notes:
- `-O` flag: Forces SCP protocol (required for older systems)
- `-o HostKeyAlgorithms=+ssh-rsa`: Allows RSA keys
- `-o PubkeyAcceptedKeyTypes=+ssh-rsa`: Accepts RSA public keys
- Target directory: `~/` (root home directory)

## Video Streaming

### Camera Information
- **Device Path**: `/dev/video13`
- **Camera Model**: Intel RealSense R200
- **Default Resolution**: 640x480 @ 30fps
- **Supported Resolutions**: 320x240, 640x480, 1280x720, 1920x1080

### GStreamer Support
The Intel Aero has GStreamer 1.0 pre-installed with hardware encoding support.

### Available Video Encoders
```bash
# Hardware encoders (best performance)
vaapih264enc     # VA-API H.264 encoder (Intel hardware)
vaapih265enc     # VA-API H.265 encoder
vaapimpeg2enc    # VA-API MPEG-2 encoder
vaapijpegenc     # VA-API JPEG encoder
vaapivp8enc      # VA-API VP8 encoder

# Software encoders
jpegenc          # JPEG image encoder
theoraenc        # Theora video encoder
pngenc           # PNG image encoder
webpenc          # WEBP image encoder
```

### Live Streaming to PC (Recommended Method)

**On Drone:**
```bash
# Kill mavlink_bridge first
killall python2

# Stream via UDP using hardware H.264 encoder
gst-launch-1.0 \
  v4l2src device=/dev/video13 ! \
  video/x-raw,width=640,height=480,framerate=30/1 ! \
  videoconvert ! \
  vaapih264enc rate-control=cbr bitrate=1200 ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=192.168.1.2 port=5000
```

**On Windows PC (with VLC):**
```powershell
vlc udp://@:5000 --network-caching=50
```

### Alternative Streaming Methods

#### MJPEG Stream (More Compatible)
```bash
gst-launch-1.0 \
  v4l2src device=/dev/video13 ! \
  video/x-raw,width=640,height=480,framerate=30/1 ! \
  videoconvert ! \
  jpegenc quality=80 ! \
  rtpjpegpay ! \
  udpsink host=192.168.1.2 port=5000
```

View with: `vlc rtp://192.168.1.2:5000`

#### Higher Quality (1280x720)
```bash
gst-launch-1.0 \
  v4l2src device=/dev/video13 ! \
  video/x-raw,width=1280,height=720,framerate=30/1 ! \
  videoconvert ! \
  vaapih264enc rate-control=cbr bitrate=2000 ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=192.168.1.2 port=5000
```

### Streaming Performance
- **Latency**: ~50-100ms with H.264, ~100-200ms with MJPEG
- **Bitrate**: 800-1200 kbps for 640x480, 1500-2500 kbps for 1280x720
- **CPU Usage**: <15% with hardware encoding (vaapih264enc)
- **Battery Impact**: ~5-10% additional drain

### Recording on Drone

**Record to File:**
```bash
gst-launch-1.0 \
  v4l2src device=/dev/video13 ! \
  video/x-raw,width=640,height=480,framerate=30/1 ! \
  videoconvert ! \
  vaapih264enc ! \
  h264parse ! \
  mp4mux ! \
  filesink location=/home/root/flight_$(date +%s).mp4
```

**Stream and Record Simultaneously:**
```bash
gst-launch-1.0 \
  v4l2src device=/dev/video13 ! \
  video/x-raw,width=640,height=480,framerate=30/1 ! \
  videoconvert ! \
  tee name=t \
  t. ! queue ! vaapih264enc ! rtph264pay ! udpsink host=192.168.1.2 port=5000 \
  t. ! queue ! vaapih264enc ! mp4mux ! filesink location=/home/root/recording.mp4
```

### Checking Stream Status

```bash
# Check if stream is running
ps | grep gst-launch

# Monitor network traffic
ifconfig wlan0

# Test camera availability
ls -l /dev/video*
```

## Flight Control

### Flight Modes
Available through DroneKit:
- `GUIDED` - Autopilot-assisted flight (safest for autonomous operations)
- `STABILIZE` - Manual control with stabilization
- `LAND` - Automatic landing mode
- `LOITER` - Hold position (requires GPS)
- `ALT_HOLD` - Hold altitude only

### Setting Mode
```python
from dronekit import VehicleMode
vehicle.mode = VehicleMode("GUIDED")

# Wait for mode change
while vehicle.mode.name != "GUIDED":
    time.sleep(0.5)
```

### Arming/Disarming
```python
# Check if armable
if vehicle.is_armable:
    vehicle.armed = True
    
# Wait for arming
while not vehicle.armed:
    time.sleep(0.5)

# Disarm
vehicle.armed = False
```

### NED Velocity Commands (Safer than RC Override)

```python
from pymavlink import mavutil

msg = vehicle.message_factory.set_position_target_local_ned_encode(
    0,       # time_boot_ms (not used)
    0, 0,    # target system, target component
    mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
    0b0000111111000111,  # type_mask (only speeds enabled)
    0, 0, 0,  # x, y, z positions (not used)
    velocity_x, velocity_y, velocity_z,  # velocities in m/s
    0, 0, 0,  # x, y, z acceleration (not used)
    0, 0)     # yaw, yaw_rate (not used)

vehicle.send_mavlink(msg)
```

**NED Frame Convention**:
- **North** (X): Forward
- **East** (Y): Right
- **Down** (Z): Downward (negative = up!)
  - `velocity_z = -0.5` → Climb at 0.5 m/s
  - `velocity_z = 0.5` → Descend at 0.5 m/s

## Battery Information

### Getting Battery Level
```python
def get_battery_percentage(vehicle):
    if vehicle.battery:
        # Direct battery level
        if vehicle.battery.level is not None:
            return vehicle.battery.level
        
        # Estimate from voltage (4S LiPo: 16.8V=100%, 14.0V=0%)
        elif vehicle.battery.voltage is not None:
            voltage = vehicle.battery.voltage
            percentage = ((voltage - 14.0) / (16.8 - 14.0)) * 100
            return max(0, min(100, percentage))
    return None
```

### Battery Properties
```python
vehicle.battery.voltage      # Current voltage
vehicle.battery.current      # Current draw (amps)
vehicle.battery.level        # Percentage (0-100)
```

## System Commands (Yocto Linux)

### Process Management
```bash
# List processes
ps

# Kill specific process
kill <PID>

# Kill all processes by name
killall <process_name>

# Kill Python processes
killall python2
```

**Note**: `pkill` command is NOT available on Yocto

### File System
```bash
# List files
ls -la

# Navigate
cd /path/to/directory

# Remove file
rm filename

# View file
cat filename

# Edit file (vi editor)
vi filename
```

## Python Version & Compatibility

- **Python Version**: Python 2.7
- **Print Statements**: Use `print "text"` (no parentheses required, but work)
- **String Formatting**: Use `%` formatting: `"Value: %.2f" % value`
- **Exception Handling**: Old-style `except Exception, e:` or new-style `except Exception as e:`

### Key Installed Packages
- `dronekit` - DroneKit Python library
- `pymavlink` - MAVLink protocol implementation
- `json` - JSON encoding/decoding
- `time` - Time functions
- `math` - Mathematical functions
- `gstreamer1.0` - Media streaming framework
- `gstreamer1.0-vaapi` - Hardware video encoding/decoding
- `opencv-python` - Computer vision library (with GStreamer support)

## Created Scripts

### 1. `autonomous_flight.py`
Full autonomous flight script:
- Ascends to 0.5m altitude
- Hovers for 5 seconds
- Lands gently
- Records flight statistics
- Uses custom altitude filter
- Uses NED velocity commands in GUIDED mode

### 2. `stream_altitude.py`
Continuous altitude streaming:
- Reports altitude every second (indefinitely)
- JSON output format
- Custom altitude filtering
- Debug mode available (`--debug` flag)
- Error recovery and connection monitoring

### 3. `alt_read.py`
Simple altitude reader using DroneKit built-in properties:
- Runs for 15 seconds
- Reports every second
- Uses `vehicle.location.global_relative_frame.alt`
- Simpler than custom filtering approach

### 4. `drone_info.py`
System information script (assumed to exist based on context)

## Flight Statistics JSON Format

```json
{
  "flight_id": 1234567890,
  "drone_id": 1,
  "start_time": "2016-10-29 08:30:00",
  "end_time": "2016-10-29 08:35:30",
  "max_altitude": 0.52,
  "start_battery_percentage": 85,
  "end_battery_percentage": 78,
  "duration": 5.5
}
```

## Important Safety Notes

### Pre-flight Checks
1. Check battery level (minimum 30%)
2. Verify `vehicle.is_armable` is True
3. Confirm correct flight mode
4. Initialize altitude filter before flight
5. Test emergency landing procedures

### Recommended Flight Parameters
- **Target Altitude**: 0.5 - 1.0 meters (indoor testing)
- **Climb Rate**: 0.3 m/s (gentle)
- **Descent Rate**: 0.2 m/s (gentle)
- **Altitude Tolerance**: 0.05 meters
- **Landing Descent**: 0.1 m/s (very gentle)

### Emergency Procedures
```python
try:
    # Flight operations
    pass
except:
    # Stop all movement
    send_ned_velocity(vehicle, 0, 0, 0, duration=0.5)
    # Switch to LAND mode
    vehicle.mode = VehicleMode("LAND")
    time.sleep(2)
    vehicle.armed = False
```

## Network Configuration

- **Drone IP**: 192.168.1.1
- **Ground Station IP**: 192.168.1.2 (expected by mavlink_bridge)
- **WiFi**: Intel Aero creates its own access point
- **SSH Port**: 22 (default)

## Additional System Processes

### Key Running Services
- `udevd` - Device manager
- `dbus-daemon` - Inter-process communication
- `NetworkManager` - Network management
- `bluetoothd` - Bluetooth service
- `gpsd` - GPS daemon
- `hostapd` - WiFi access point
- `Xorg` - Display server
- `mavlink_bridge.py` - MAVLink forwarding (conflicts with direct access)

## Troubleshooting Checklist

- [ ] Is `mavlink_bridge.py` killed?
- [ ] Is battery above 30%?
- [ ] Are you connected via SSH to 192.168.1.1?
- [ ] Is the correct Python version (2.7) being used?
- [ ] Did you wait 2+ seconds after connecting?
- [ ] Is the baud rate set to 1500000?
- [ ] Are you using the correct port (`/dev/ttyS1`)?
- [ ] Is the drone in the correct mode (GUIDED for autonomous)?
- [ ] Did you initialize the altitude filter before use?
- [ ] Are you handling MAVLink errors properly?
- [ ] Is the camera device available (`/dev/video13`)?
- [ ] Is another process using the camera? (check with `ps | grep gst`)

## Video Streaming Troubleshooting

### No Video Stream
```bash
# Check camera device
ls -l /dev/video*

# Test camera with simple capture
gst-launch-1.0 v4l2src device=/dev/video13 num-buffers=1 ! fakesink

# Kill any processes using camera
killall python2
killall gst-launch-1.0
```

### Choppy/Laggy Stream
- Reduce bitrate: Change `bitrate=1200` to `bitrate=800`
- Lower resolution: Use 320x240 instead of 640x480
- Check WiFi signal strength: Move closer to drone
- Reduce VLC caching: Use `--network-caching=0`

### Stream Disconnects
- Increase bitrate control buffer
- Use TCP instead of UDP (add `protocol=tcp` to udpsink)
- Check PC IP is correct (should be 192.168.1.2)

### "No element" Error
- Check encoder availability: `gst-inspect-1.0 vaapih264enc`
- Use alternative encoder if needed (jpegenc for MJPEG)
- Install missing plugins: `opkg install gstreamer1.0-plugins-bad`

## Future Improvements

### Potential Enhancements
1. Add GPS position tracking
2. Implement waypoint navigation
3. Add obstacle detection integration
4. Log flight data to database
5. ~~Implement real-time video streaming~~ ✅ **COMPLETED**
6. Add pigeon detection integration with live stream
7. Create web-based mission planner
8. Add telemetry dashboard with video overlay
9. Implement geofencing
10. Add battery monitoring alerts
11. Stream telemetry data alongside video (altitude, battery, GPS on OSD)
12. Implement automatic recording on pigeon detection
13. Add object tracking overlay on video stream

### Known Limitations
- Altitude sensor has drift without GPS
- Indoor flight requires visual odometry or other positioning
- MAVLink connection can be unstable with multiple processes
- No built-in collision avoidance
- Limited battery life (~15-20 minutes flight time)

## References & Documentation

- [DroneKit Python Documentation](http://python.dronekit.io/)
- [MAVLink Protocol](https://mavlink.io/en/)
- [Intel Aero Documentation](https://github.com/intel-aero)
- [ArduPilot Documentation](https://ardupilot.org/)

---

**Document Created**: December 30, 2025  
**Project**: Scarecrow Drone  
**Repository**: HadidaSE/scarecrow_drone  
**Branch**: master
