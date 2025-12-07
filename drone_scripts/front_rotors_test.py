#!/usr/bin/env python2.7
"""
Motor Speed Control Test for Intel Aero RTF Drone
Tests 3 different power levels: 33%, 66%, 100%
Each level runs for 3 seconds
Compatible with Python 2.7 and Yocto factory version
"""

import time
import sys

try:
    from pymavlink import mavutil
except ImportError:
    print "Error: pymavlink module not found"
    print "Please install pymavlink: pip install pymavlink"
    sys.exit(1)


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
    print "Throttle armed"


def disarm_throttle(master):
    """Disarm the drone throttle"""
    print "Disarming throttle..."
    master.arducopter_disarm()
    master.motors_disarmed_wait()
    print "Throttle disarmed"


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


if __name__ == "__main__":
    print "="*50
    print "Intel Aero Motor Speed Control Test"
    print "="*50
    print "WARNING: Ensure drone is secured!"
    print "Testing 3 power levels:"
    print "  1. 33%% power for 3 seconds"
    print "  2. 66%% power for 3 seconds"
    print "  3. 100%% power for 3 seconds"
    print "Starting in 2 seconds..."
    print ""
    time.sleep(2)

    # Connect to flight controller
    print "Connecting to flight controller on /dev/ttyS1..."
    try:
        master = mavutil.mavlink_connection('/dev/ttyS1', baud=1500000)
        master.wait_heartbeat()
        print "Connected! System %u Component %u" % (master.target_system, master.target_component)
    except Exception as e:
        print "Error connecting: %s" % str(e)
        sys.exit(1)

    # PWM values
    NEUTRAL = 1500
    THROTTLE_MIN = 1000
    THROTTLE_33 = 1300   # 33% power
    THROTTLE_66 = 1600   # 66% power
    THROTTLE_100 = 1900  # 100% power

    try:
        # Set mode
        set_mode(master, 'STABILIZED')
        time.sleep(1)

        # Arm
        arm_throttle(master)
        time.sleep(1)

        # Test Level 1: 33% power
        print "\n>>> LEVEL 1: 33%% POWER FOR 3 SECONDS <<<"
        rc_channels = [NEUTRAL, NEUTRAL, THROTTLE_33, NEUTRAL, 0, 0, 0, 0]
        set_rc_override(master, rc_channels)
        time.sleep(3)

        # Return to minimum
        rc_channels[2] = THROTTLE_MIN
        set_rc_override(master, rc_channels)
        time.sleep(1)

        # Test Level 2: 66% power
        print ">>> LEVEL 2: 66%% POWER FOR 3 SECONDS <<<"
        rc_channels[2] = THROTTLE_66
        set_rc_override(master, rc_channels)
        time.sleep(3)

        # Return to minimum
        rc_channels[2] = THROTTLE_MIN
        set_rc_override(master, rc_channels)
        time.sleep(1)

        # Test Level 3: 100% power
        print ">>> LEVEL 3: 100%% POWER FOR 3 SECONDS <<<"
        rc_channels[2] = THROTTLE_100
        set_rc_override(master, rc_channels)
        time.sleep(3)

        # Stop
        print ">>> STOPPING ALL MOTORS <<<"
        rc_channels[2] = THROTTLE_MIN
        set_rc_override(master, rc_channels)
        time.sleep(0.5)

        release_rc_override(master)
        time.sleep(0.5)

        # Disarm
        disarm_throttle(master)

        print "\n" + "="*50
        print "TEST COMPLETED SUCCESSFULLY!"
        print "All 3 power levels tested"
        print "="*50

    except KeyboardInterrupt:
        print "\nInterrupted by user"
        release_rc_override(master)
        disarm_throttle(master)

    except Exception as e:
        print "Error: %s" % str(e)
        try:
            release_rc_override(master)
            disarm_throttle(master)
        except:
            pass
        sys.exit(1)

    finally:
        master.close()
