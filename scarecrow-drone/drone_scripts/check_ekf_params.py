#!/usr/bin/env python
"""
check_ekf_params.py - Check and optionally set EKF/arming parameters for indoor flight
Run with --fix to automatically set parameters for indoor (no GPS) flight
Compatible with Python 2.7
"""
from __future__ import print_function
import os
import signal
import subprocess
import sys
import time

try:
    from dronekit import connect
except ImportError:
    print("ERROR: dronekit not installed")
    sys.exit(1)

CONNECTION_STRING = "/dev/ttyS1"
BAUD_RATE = 1500000
bridge_was_running = False


def kill_mavlink_bridge():
    """Kill mavlink_bridge.py if it's holding the serial port"""
    global bridge_was_running
    print("Checking for mavlink_bridge holding serial port...")
    try:
        result = subprocess.Popen(['fuser', '/dev/ttyS1'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        pids = stdout.strip().split()
        if pids:
            for pid in pids:
                pid = pid.strip()
                if pid:
                    print("Killing process %s holding /dev/ttyS1..." % pid)
                    os.kill(int(pid), signal.SIGKILL)
                    bridge_was_running = True
            time.sleep(0.5)
            print("mavlink_bridge killed")
        else:
            print("No process holding /dev/ttyS1")
    except Exception as e:
        print("Note: Could not check/kill bridge: %s" % e)


def restart_mavlink_bridge():
    """Restart mavlink_bridge if we killed it"""
    global bridge_was_running
    if bridge_was_running:
        print("Restarting mavlink_bridge...")
        try:
            subprocess.Popen(['python2', '/usr/sbin/mavlink_bridge.py', '192.168.1.2'],
                           stdout=open('/dev/null', 'w'),
                           stderr=open('/dev/null', 'w'))
            print("mavlink_bridge restarted")
        except Exception as e:
            print("Warning: Could not restart bridge: %s" % e)

# Parameters to check for indoor flight
PARAMS_TO_CHECK = [
    ("COM_ARM_WO_GPS", 1, "Allow arming without GPS"),
    ("COM_ARM_EKF_HGT", 0.5, "EKF height check threshold (relax to 0.5)"),
    ("COM_ARM_EKF_POS", 0.5, "EKF position check threshold (relax to 0.5)"),
    ("COM_ARM_EKF_VEL", 0.5, "EKF velocity check threshold (relax to 0.5)"),
    ("EKF2_AID_MASK", None, "EKF sensor mask (info only)"),
    ("SYS_MC_EST_GROUP", None, "Estimator group (info only)"),
]

def main():
    fix_mode = "--fix" in sys.argv

    print("=" * 60)
    print("EKF/Arming Parameter Checker")
    if fix_mode:
        print("MODE: FIX - Will set parameters for indoor flight")
    else:
        print("MODE: CHECK - Run with --fix to set parameters")
    print("=" * 60)

    print("\nConnecting to %s..." % CONNECTION_STRING)
    vehicle = connect(CONNECTION_STRING, baud=BAUD_RATE, wait_ready=False)
    time.sleep(2)

    print("Connected! Mode: %s" % vehicle.mode.name)
    print("EKF OK: %s" % vehicle.ekf_ok)
    print("Is Armable: %s" % vehicle.is_armable)

    # Check GPS status
    gps = vehicle.gps_0
    if gps:
        print("GPS: fix_type=%s, satellites=%s" % (gps.fix_type, gps.satellites_visible))
    else:
        print("GPS: No data")

    print("\n" + "-" * 60)
    print("Parameter Check:")
    print("-" * 60)

    changes_needed = []

    for param_name, recommended, description in PARAMS_TO_CHECK:
        try:
            current = vehicle.parameters[param_name]
            status = "OK"

            if recommended is not None:
                if param_name == "COM_ARM_WO_GPS":
                    # This should be 1 (allow) for indoor
                    if current != 1:
                        status = "NEEDS FIX (should be 1)"
                        changes_needed.append((param_name, 1))
                elif current > recommended:
                    # Threshold params - lower is more relaxed
                    status = "NEEDS FIX (should be <= %.1f)" % recommended
                    changes_needed.append((param_name, recommended))

            print("  %s = %s  [%s] - %s" % (param_name, current, status, description))

        except Exception as e:
            print("  %s = NOT FOUND - %s" % (param_name, description))

    if fix_mode and changes_needed:
        print("\n" + "-" * 60)
        print("Applying fixes...")
        print("-" * 60)

        for param_name, new_value in changes_needed:
            try:
                print("  Setting %s = %s..." % (param_name, new_value))
                vehicle.parameters[param_name] = new_value
                time.sleep(0.5)
                # Verify
                actual = vehicle.parameters[param_name]
                if actual == new_value:
                    print("    SUCCESS: %s = %s" % (param_name, actual))
                else:
                    print("    WARNING: Value is %s (expected %s)" % (actual, new_value))
            except Exception as e:
                print("    ERROR: %s" % e)

        print("\nParameters updated! You may need to reboot the drone for changes to take effect.")

    elif changes_needed:
        print("\n%d parameter(s) need adjustment. Run with --fix to apply." % len(changes_needed))
    else:
        print("\nAll parameters look good for indoor flight!")

    # Final EKF status
    print("\n" + "-" * 60)
    print("Final Status:")
    print("-" * 60)
    time.sleep(1)
    print("  EKF OK: %s" % vehicle.ekf_ok)
    print("  Is Armable: %s" % vehicle.is_armable)

    vehicle.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
