#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Autonomous Altitude Control - Intel Aero RTF Drone
Maintains target altitude using calibrated PWM values
Controls: Y=Start, X=Land, Z=Emergency Stop
"""

from pymavlink import mavutil
import sys
import tty
import termios
import time
import select
from flight_constants import *


def set_rc_override(master, channels):
    """Override RC channels to control motors"""
    master.mav.rc_channels_override_send(
        master.target_system,
        master.target_component,
        channels[0], channels[1], channels[2], channels[3],
        channels[4], channels[5], channels[6], channels[7]
    )


def release_rc_override(master):
    """Release RC override"""
    master.mav.rc_channels_override_send(
        master.target_system,
        master.target_component,
        0, 0, 0, 0, 0, 0, 0, 0
    )


def arm_throttle(master):
    """Arm the drone throttle"""
    print "Arming throttle..."
    master.arducopter_arm()
    master.motors_armed_wait()
    print "ARMED!"


def disarm_throttle(master):
    """Disarm the drone throttle"""
    print "Disarming throttle..."
    master.arducopter_disarm()
    master.motors_disarmed_wait()
    print "DISARMED"


def set_mode(master, mode):
    """Set flight mode"""
    mode_mapping = master.mode_mapping()
    if mode not in mode_mapping:
        print "Unknown mode: %s" % mode
        print "Available modes:", mode_mapping.keys()
        sys.exit(1)

    mode_id = mode_mapping[mode]
    if isinstance(mode_id, tuple):
        mode_id = mode_id[0]
    mode_id = int(mode_id)

    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )
    print "Mode set to %s" % mode


def get_altitude(master):
    """Get current altitude from LOCAL_POSITION_NED"""
    try:
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False, timeout=0.01)
        if msg:
            return -msg.z  # Negative Z is altitude (NED frame)
    except:
        pass
    return None


def establish_home_altitude(master):
    """Get baseline home altitude by averaging multiple readings"""
    print "Establishing home altitude..."
    readings = []
    for _ in range(50):  # 50 readings over 1 second
        alt = get_altitude(master)
        if alt is not None:
            readings.append(alt)
        time.sleep(0.02)

    if len(readings) > 0:
        home_alt = sum(readings) / float(len(readings))
        print "Home altitude: %.3f meters" % home_alt
        return home_alt
    else:
        print "WARNING: Could not establish home altitude, using 0.0"
        return 0.0


def wait_for_keypress(key):
    """Wait for specific key press"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if ch.upper() == key.upper():
                    return True
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def autonomous_flight():
    """
    Main autonomous altitude control function
    """
    print "="*60
    print "AUTONOMOUS ALTITUDE CONTROL - INTEL AERO"
    print "="*60
    print ""
    print "WARNING: Ensure drone is secured and area is clear!"
    print ""

    # Get target altitude from user
    try:
        target_input = raw_input("Enter target altitude in meters [default: %.1f]: " % DEFAULT_TARGET_ALTITUDE)
        if target_input.strip():
            target_altitude = float(target_input)
        else:
            target_altitude = DEFAULT_TARGET_ALTITUDE
    except:
        target_altitude = DEFAULT_TARGET_ALTITUDE

    print "\nTarget altitude: %.2f meters" % target_altitude
    print ""

    master = None
    flight_start_time = None
    max_altitude = 0.0

    try:
        # ============================================================
        # CONNECTION PHASE
        # ============================================================
        print "Connecting to flight controller on %s..." % SERIAL_PORT
        master = mavutil.mavlink_connection(SERIAL_PORT, baud=BAUD_RATE)
        master.wait_heartbeat()
        print "Connected! System %u Component %u" % (master.target_system, master.target_component)
        time.sleep(1)

        # ============================================================
        # INITIALIZATION PHASE
        # ============================================================
        set_mode(master, FLIGHT_MODE)
        time.sleep(1)

        arm_throttle(master)
        time.sleep(1)

        home_altitude = establish_home_altitude(master)

        # ============================================================
        # READY STATE
        # ============================================================
        print "\n" + "="*60
        print "READY TO FLY"
        print "="*60
        print "Controls:"
        print "  Y = Start autonomous flight"
        print "  X = Controlled landing (during flight)"
        print "  Z = Emergency shutdown"
        print "="*60
        print ""

        # Set motors to minimum (armed but not spinning)
        rc_channels = [NEUTRAL, NEUTRAL, THROTTLE_MIN, NEUTRAL, 0, 0, 0, 0]
        set_rc_override(master, rc_channels)

        print "Motors armed at minimum throttle"
        print "\nPRESS 'Y' TO START AUTONOMOUS FLIGHT"

        # Wait for Y key
        wait_for_keypress('Y')

        # ============================================================
        # TAKEOFF PHASE
        # ============================================================
        print "\n" + "="*60
        print "STARTING AUTONOMOUS FLIGHT"
        print "Target altitude: %.2f meters" % target_altitude
        print "="*60
        print ""

        flight_start_time = time.time()

        # Start climbing
        current_throttle = CLIMB_PWM
        rc_channels[2] = current_throttle
        set_rc_override(master, rc_channels)

        # ============================================================
        # AUTONOMOUS HOVER PHASE (Main Loop)
        # ============================================================
        last_status_time = time.time()
        last_override_time = time.time()
        current_mode = "CLIMBING"

        # Set terminal to cbreak mode for keyboard input
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(sys.stdin.fileno())

            while True:
                current_time = time.time()

                # Get current altitude
                raw_alt = get_altitude(master)

                if raw_alt is not None:
                    relative_alt = raw_alt - home_altitude

                    # Track max altitude
                    if relative_alt > max_altitude:
                        max_altitude = relative_alt

                    # Determine required throttle based on altitude
                    if relative_alt < (target_altitude - ALTITUDE_TOLERANCE):
                        # Below target - climb
                        required_throttle = CLIMB_PWM
                        mode = "CLIMBING"
                    elif relative_alt > (target_altitude + ALTITUDE_TOLERANCE):
                        # Above target - descend
                        required_throttle = LAND_PWM
                        mode = "DESCENDING"
                    else:
                        # At target - hover
                        required_throttle = HOVER_PWM
                        mode = "HOVERING"

                    # Update throttle if changed
                    if required_throttle != current_throttle:
                        current_throttle = required_throttle
                        current_mode = mode
                        rc_channels[2] = current_throttle
                        set_rc_override(master, rc_channels)
                        last_override_time = current_time

                    # Print status update
                    if current_time - last_status_time >= STATUS_UPDATE_RATE:
                        timestamp = time.strftime("%H:%M:%S")
                        print "[%s] ALT: %.3fm | MODE: %s | PWM: %d" % (
                            timestamp, relative_alt, current_mode, current_throttle
                        )
                        last_status_time = current_time

                # Refresh RC override periodically
                if current_time - last_override_time >= RC_OVERRIDE_REFRESH_RATE:
                    set_rc_override(master, rc_channels)
                    last_override_time = current_time

                # Check for keyboard input
                if select.select([sys.stdin], [], [], 0)[0]:
                    ch = sys.stdin.read(1)

                    # X = Start landing
                    if ch.upper() == 'X':
                        print "\n" + "="*60
                        print "LANDING INITIATED"
                        print "="*60
                        break

                    # Z = Emergency shutdown
                    elif ch.upper() == 'Z':
                        print "\n" + "="*60
                        print "EMERGENCY SHUTDOWN"
                        print "="*60
                        raise KeyboardInterrupt

                # Sample at high rate
                time.sleep(ALTITUDE_SAMPLE_RATE)

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        # ============================================================
        # LANDING PHASE
        # ============================================================
        print "\nControlled descent initiated..."
        rc_channels[2] = LAND_PWM
        set_rc_override(master, rc_channels)

        # Monitor descent
        while True:
            raw_alt = get_altitude(master)
            if raw_alt is not None:
                relative_alt = raw_alt - home_altitude

                timestamp = time.strftime("%H:%M:%S")
                print "[%s] LANDING - ALT: %.3fm | PWM: %d" % (
                    timestamp, relative_alt, LAND_PWM
                )

                # Check if close to ground
                if relative_alt < LANDING_ALTITUDE_THRESHOLD:
                    print "\nNear ground - reducing to minimum throttle..."
                    rc_channels[2] = THROTTLE_MIN
                    set_rc_override(master, rc_channels)
                    time.sleep(2)
                    break

            time.sleep(STATUS_UPDATE_RATE)

        # ============================================================
        # SHUTDOWN PHASE
        # ============================================================
        print "\nReleasing RC override..."
        release_rc_override(master)
        time.sleep(0.5)

        disarm_throttle(master)

        # Print summary
        if flight_start_time:
            flight_duration = time.time() - flight_start_time
            print "\n" + "="*60
            print "FLIGHT COMPLETE"
            print "="*60
            print "Flight duration: %.1f seconds" % flight_duration
            print "Max altitude reached: %.3f meters" % max_altitude
            print "Target altitude: %.3f meters" % target_altitude
            print "="*60

    except KeyboardInterrupt:
        print "\n\nEMERGENCY STOP ACTIVATED!"
        if master:
            # Immediate shutdown
            rc_channels = [NEUTRAL, NEUTRAL, THROTTLE_MIN, NEUTRAL, 0, 0, 0, 0]
            set_rc_override(master, rc_channels)
            time.sleep(0.5)
            release_rc_override(master)
            try:
                disarm_throttle(master)
            except:
                pass

    except Exception as e:
        print "\nERROR: %s" % str(e)
        import traceback
        traceback.print_exc()
        if master:
            rc_channels = [NEUTRAL, NEUTRAL, THROTTLE_MIN, NEUTRAL, 0, 0, 0, 0]
            set_rc_override(master, rc_channels)
            release_rc_override(master)
            try:
                disarm_throttle(master)
            except:
                pass

    finally:
        if master:
            release_rc_override(master)
            print "\nClosing connection..."
            master.close()
            print "Connection closed"


if __name__ == "__main__":
    autonomous_flight()
