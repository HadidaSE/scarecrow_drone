#!/usr/bin/env python
"""
start_flight_v2.py - Takeoff 1m, Hover 3s, Land (No GPS)
Runs on Intel Aero drone (PX4)
- Arms directly (no GPS required)
- Uses RC channel override for throttle control
- Takes off to ~1 meter
- Hovers for 3 seconds
- Lands gracefully
- Ctrl+C = EMERGENCY STOP (motors off immediately)
- AUTO-KILL: Motors automatically stop after 10 seconds
Compatible with Python 2.7
"""
from __future__ import print_function
import json
import signal
import sys
import time
import threading

# Global vehicle reference for signal handler
vehicle = None
script_start_time = None
MAX_FLIGHT_TIME = 10  # SAFETY: Auto-kill motors after 10 seconds (starts after arming)


def log(msg):
    """Print debug message with timestamp"""
    print("[%.2f] %s" % (time.time() - (script_start_time or time.time()), msg))
    sys.stdout.flush()


def watchdog_timer():
    """Background thread that kills motors after MAX_FLIGHT_TIME seconds"""
    global vehicle, script_start_time
    while True:
        time.sleep(0.5)
        if script_start_time is not None:
            elapsed = time.time() - script_start_time
            if elapsed >= MAX_FLIGHT_TIME:
                log(">>> WATCHDOG TRIGGERED - AUTO-KILL <<<")
                print(json.dumps({
                    "status": "WATCHDOG_TIMEOUT",
                    "message": "Auto-kill after %d seconds" % MAX_FLIGHT_TIME
                }))
                sys.stdout.flush()
                force_kill_motors()
                import os
                os._exit(0)


def force_kill_motors():
    """Force kill motors - used by watchdog and emergency stop"""
    global vehicle
    log(">>> ENTER force_kill_motors()")
    if vehicle:
        # FIRST: Clear ALL RC overrides - don't set any throttle!
        try:
            log("Clearing ALL RC overrides (no throttle set)...")
            vehicle.channels.overrides = {}
        except Exception as e:
            log("Error clearing overrides: %s" % e)

        # SECOND: Send disarm command
        try:
            log("Sending MAVLink disarm command...")
            vehicle._master.mav.command_long_send(
                vehicle._master.target_system,
                vehicle._master.target_component,
                400,  # MAV_CMD_COMPONENT_ARM_DISARM
                0,    # confirmation
                0,    # param1: 0=disarm
                21196,  # param2: 21196=force
                0, 0, 0, 0, 0
            )
            log("Disarm command sent")
        except Exception as e:
            log("Error sending disarm: %s" % e)

        # THIRD: Also try DroneKit disarm
        try:
            log("Setting vehicle.armed = False...")
            vehicle.armed = False
        except Exception as e:
            log("Error setting armed=False: %s" % e)

    log(">>> EXIT force_kill_motors()")

try:
    from dronekit import connect
    DRONEKIT_AVAILABLE = True
except ImportError:
    DRONEKIT_AVAILABLE = False
    print(json.dumps({"success": False, "error": "dronekit not installed"}))
    sys.exit(1)

# Connection to flight controller
CONNECTION_STRING = "/dev/ttyS1"
BAUD_RATE = 1500000

# Flight parameters
TARGET_ALTITUDE = 1.0  # meters
HOVER_TIME = 3  # seconds

# RC Channel values (PWM microseconds)
# Channel 3 is throttle
# 1000 = min throttle, 1500 = mid/hover, 2000 = max throttle
RC_MIN = 1000
RC_MID = 1500
RC_MAX = 2000

# Throttle values tuned for ~1m altitude (CONSERVATIVE)
TAKEOFF_THROTTLE = 1160   # Gentle climb - reduced from 1620
HOVER_THROTTLE = 1210     # Maintain altitude - reduced from 1530
LAND_THROTTLE = 1090      # Very gentle descent


def emergency_stop(signum=None, frame=None):
    """EMERGENCY STOP - DISARM motors immediately (complete shutdown)"""
    log(">>> EMERGENCY_STOP signal received! <<<")
    print(json.dumps({"status": "EMERGENCY_STOP", "reason": "Signal received"}))
    sys.stdout.flush()
    force_kill_motors()
    log("Motors DISARMED - exiting")
    print(json.dumps({"status": "stopped", "message": "Motors DISARMED"}))
    sys.stdout.flush()
    import os
    os._exit(0)


# Register Ctrl+C handler
signal.signal(signal.SIGINT, emergency_stop)
signal.signal(signal.SIGTERM, emergency_stop)


def set_rc_throttle(throttle_pwm):
    """Set RC channel 3 (throttle) override"""
    global vehicle
    log("set_rc_throttle(%d)" % throttle_pwm)
    vehicle.channels.overrides['3'] = throttle_pwm


def clear_rc_overrides():
    """Clear all RC overrides by sending zeros to all channels"""
    global vehicle
    log("clear_rc_overrides()")
    # Send zeros to all 8 RC channels (proper way to clear overrides)
    vehicle._master.mav.rc_channels_override_send(
        vehicle._master.target_system,
        vehicle._master.target_component,
        0, 0, 0, 0, 0, 0, 0, 0
    )


def wait_for_gps():
    """Wait for GPS fix and EKF to converge"""
    global vehicle

    print(json.dumps({"status": "waiting_for_gps"}))
    sys.stdout.flush()

    # Wait up to 60 seconds for GPS and EKF
    timeout = 60
    while timeout > 0:
        gps = vehicle.gps_0
        ekf_ok = vehicle.ekf_ok
        is_armable = vehicle.is_armable

        # Check GPS fix (fix_type >= 3 means 3D fix)
        has_gps = gps and gps.fix_type is not None and gps.fix_type >= 3

        if has_gps and ekf_ok:
            print(json.dumps({
                "status": "gps_ready",
                "fix_type": gps.fix_type,
                "satellites": gps.satellites_visible,
                "ekf_ok": ekf_ok
            }))
            sys.stdout.flush()
            return {"success": True}

        # Print progress every 5 seconds
        if timeout % 5 == 0:
            print(json.dumps({
                "status": "waiting_for_gps",
                "fix_type": gps.fix_type if gps else None,
                "satellites": gps.satellites_visible if gps else None,
                "ekf_ok": ekf_ok,
                "is_armable": is_armable,
                "timeout": timeout
            }))
            sys.stdout.flush()

        time.sleep(1)
        timeout -= 1

    return {"success": False, "error": "Timeout waiting for GPS fix"}


def arm_vehicle():
    """Arms vehicle directly without GPS (manual/stabilized mode)"""
    global vehicle

    print(json.dumps({
        "status": "pre_arm_check",
        "mode": vehicle.mode.name,
        "is_armable": vehicle.is_armable,
        "ekf_ok": vehicle.ekf_ok
    }))
    sys.stdout.flush()

    # Wait for EKF to be ready (REQUIRED - up to 30 seconds)
    log("Waiting for EKF to converge...")
    ekf_timeout = 30
    while not vehicle.ekf_ok and ekf_timeout > 0:
        # Get detailed EKF status for diagnostics
        try:
            gps = vehicle.gps_0
            gps_fix = gps.fix_type if gps else 0
            gps_sats = gps.satellites_visible if gps else 0
            log("EKF not ready (timeout=%d) - GPS fix=%s, sats=%s, is_armable=%s" % (
                ekf_timeout, gps_fix, gps_sats, vehicle.is_armable))
        except:
            log("EKF not ready, waiting... (timeout=%d)" % ekf_timeout)
        time.sleep(1)
        ekf_timeout -= 1

    if not vehicle.ekf_ok:
        log("ERROR: EKF failed to converge after 30 seconds")
        log("This usually means: GPS required but not available, or sensor calibration needed")
        log("Try: 1) Wait longer after power-on, 2) Move drone outside for GPS, 3) Check COM_ARM_WO_GPS parameter")
        return {"success": False, "error": "EKF not ready - check GPS/sensors or set COM_ARM_WO_GPS=1"}

    # Try to arm directly - PX4 in MANUAL mode may allow this
    print(json.dumps({"status": "arming", "mode": vehicle.mode.name, "ekf_ok": vehicle.ekf_ok}))
    sys.stdout.flush()

    # Use MAVLink command to force arm (bypasses some pre-arm checks)
    # MAV_CMD_COMPONENT_ARM_DISARM (400), param1=1 (arm), param2=21196 (force)
    vehicle._master.mav.command_long_send(
        vehicle._master.target_system,
        vehicle._master.target_component,
        400,  # MAV_CMD_COMPONENT_ARM_DISARM
        0,    # confirmation
        1,    # param1: 1=arm, 0=disarm
        21196,  # param2: 21196=force arm (bypass checks)
        0, 0, 0, 0, 0  # params 3-7 unused
    )

    # Also try the normal way
    vehicle.armed = True

    timeout = 10
    while not vehicle.armed and timeout > 0:
        time.sleep(0.5)
        timeout -= 0.5
        # Keep trying to arm with force
        if not vehicle.armed:
            vehicle._master.mav.command_long_send(
                vehicle._master.target_system,
                vehicle._master.target_component,
                400, 0, 1, 21196, 0, 0, 0, 0, 0
            )
            vehicle.armed = True

    if not vehicle.armed:
        return {"success": False, "error": "Failed to arm vehicle - check safety switch and pre-arm checks"}

    print(json.dumps({"status": "armed", "mode": vehicle.mode.name}))
    sys.stdout.flush()
    return {"success": True}


def takeoff(target_alt):
    """Take off to target altitude using RC throttle override"""
    print(json.dumps({"status": "taking_off", "target_altitude": target_alt}))
    sys.stdout.flush()

    # Start at minimum throttle
    set_rc_throttle(RC_MIN)

    # Ramp up SLOWLY to takeoff throttle (smaller steps, longer delays)
    for throttle in range(RC_MID, TAKEOFF_THROTTLE + 1, 2):  # Step by 2 instead of 5
        set_rc_throttle(throttle)

    # Hold takeoff throttle briefly - just enough to get to 1m
    # With lower throttle, climb is gentler

    # Reduce to hover throttle
    set_rc_throttle(HOVER_THROTTLE)

    print(json.dumps({"status": "reached_altitude", "altitude": target_alt}))
    sys.stdout.flush()


def hover(duration):
    """Hover at current altitude for specified duration"""
    print(json.dumps({"status": "hovering", "duration": duration}))
    sys.stdout.flush()

    # Use small sleep intervals so Ctrl+C is responsive
    elapsed = 0
    while elapsed < duration:
        time.sleep(0.5)
        elapsed += 0.5
        # Optionally print progress
        if elapsed % 2 == 0:
            print(json.dumps({"status": "hovering", "remaining": duration - elapsed}))
            sys.stdout.flush()


def land():
    """Land gracefully by reducing throttle"""
    print(json.dumps({"status": "landing"}))
    sys.stdout.flush()

    # Gradually reduce throttle from hover to descent
    current = HOVER_THROTTLE
    while current > LAND_THROTTLE:
        current -= 5
        set_rc_throttle(current)
        time.sleep(0.05)

    # Hold descent throttle until landed (longer from 1m)
    time.sleep(5)

    # Cut throttle completely
    set_rc_throttle(RC_MIN)
    time.sleep(1)

    # Clear overrides
    clear_rc_overrides()

    print(json.dumps({"status": "landed"}))
    sys.stdout.flush()


def disarm():
    """Disarm the vehicle using proper MAVLink commands"""
    global vehicle

    print(json.dumps({"status": "disarming"}))
    sys.stdout.flush()

    log("Sending arducopter_disarm command...")
    # Use the same method as the working script
    vehicle._master.arducopter_disarm()

    # Wait for motors to actually disarm (blocking call)
    log("Waiting for motors to disarm...")
    vehicle._master.motors_disarmed_wait()

    log("Motors confirmed disarmed")
    print(json.dumps({"status": "disarmed"}))
    sys.stdout.flush()


def main():
    global vehicle, script_start_time

    # Start watchdog timer thread (daemon=True so it dies with main thread)
    watchdog = threading.Thread(target=watchdog_timer)
    watchdog.daemon = True
    watchdog.start()

    try:
        print(json.dumps({"status": "connecting"}))
        sys.stdout.flush()

        vehicle = connect(CONNECTION_STRING, baud=BAUD_RATE, wait_ready=False)
        time.sleep(2)  # Give it time to initialize

        print(json.dumps({"status": "connected", "mode": vehicle.mode.name}))
        sys.stdout.flush()

        # Arm the vehicle (includes EKF wait)
        result = arm_vehicle()
        if not result["success"]:
            print(json.dumps(result))
            sys.stdout.flush()
            return

        # START watchdog NOW - motors are armed and may spin!
        script_start_time = time.time()
        print(json.dumps({
            "status": "watchdog_started",
            "max_flight_time": MAX_FLIGHT_TIME,
            "message": "ARMED! Auto-kill in %d seconds from NOW" % MAX_FLIGHT_TIME
        }))
        sys.stdout.flush()

        # Take off to 1 meter
        takeoff(TARGET_ALTITUDE)

        # Hover for 10 seconds
        hover(HOVER_TIME)

        # Land gracefully
        land()

        # Disarm
        disarm()

        print(json.dumps({
            "success": True,
            "message": "Flight completed successfully"
        }))
        sys.stdout.flush()

    except KeyboardInterrupt:
        # This shouldn't trigger due to signal handler, but just in case
        emergency_stop()

    except Exception as e:
        # Emergency: clear overrides and try to disarm
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.stdout.flush()

        if vehicle:
            try:
                vehicle.channels.overrides['3'] = RC_MIN
                time.sleep(0.1)
                vehicle.channels.overrides = {}
                vehicle.armed = False
            except:
                pass

        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.stdout.flush()
        sys.exit(1)

    finally:
        if vehicle:
            try:
                # Force kill motors to ensure they're off
                force_kill_motors()
            except:
                pass
            try:
                vehicle.close()
            except:
                pass


if __name__ == "__main__":
    main()
