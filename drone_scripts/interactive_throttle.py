#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Interactive Throttle Control with Drift Correction - Intel Aero RTF Drone
Uses PyMAVLink RC override method with velocity-based drift correction
Automatically counteracts horizontal drift using IMU velocity feedback
UP/DOWN arrows adjust throttle, X to exit
"""

from pymavlink import mavutil
import sys
import tty
import termios
import time
import select


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


def get_velocity(master):
    """Get horizontal velocity from LOCAL_POSITION_NED"""
    try:
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False, timeout=0.01)
        if msg:
            return msg.vx, msg.vy  # vx = forward/back, vy = left/right
    except:
        pass
    return None, None


def pwm_from_percent(percent):
    """Convert percentage (0-100) to PWM (1000-2000)"""
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100
    return int(1000 + (percent / 100.0) * 1000)


def interactive_throttle():
    """
    Interactive throttle control with keyboard
    """
    current_percent = 58  # Starting at 10%
    STEP = 0.5            # 5% change per keypress
    MIN_PERCENT = 0
    MAX_PERCENT = 100

    NEUTRAL = 1500
    THROTTLE_MIN = 1000

    # Drift correction parameters (tune these for your drone)
    KP_ROLL = 40   # PWM correction per m/s for left/right drift
    KP_PITCH = 40  # PWM correction per m/s for forward/back drift
    MAX_CORRECTION = 200  # Maximum PWM correction limit

    print "="*60
    print "INTERACTIVE THROTTLE WITH DRIFT CORRECTION - INTEL AERO"
    print "="*60
    print ""
    print "Drift Correction: ENABLED (Kp_roll=%d, Kp_pitch=%d)" % (KP_ROLL, KP_PITCH)
    print "WARNING: Ensure drone is secured!"
    print "Starting in 2 seconds..."
    print ""
    time.sleep(2)

    master = None

    try:
        # Connect to flight controller
        print "Connecting to flight controller on /dev/ttyS1..."
        master = mavutil.mavlink_connection('/dev/ttyS1', baud=1500000)
        master.wait_heartbeat()
        print "Connected! System %u Component %u" % (master.target_system, master.target_component)
        time.sleep(1)

        # Set mode to STABILIZED
        set_mode(master, 'STABILIZED')
        time.sleep(1)

        # Arm throttle
        arm_throttle(master)
        time.sleep(1)

        # Set initial throttle
        current_pwm = pwm_from_percent(current_percent)
        rc_channels = [NEUTRAL, NEUTRAL, current_pwm, NEUTRAL, 0, 0, 0, 0]
        set_rc_override(master, rc_channels)
        time.sleep(0.5)

        # Interactive control
        print "\n" + "="*60
        print "CONTROLS:"
        print "  UP Arrow   = Increase throttle by 0.5%%"
        print "  DOWN Arrow = Decrease throttle by 0.5%%"
        print "  x          = Stop motors and exit"
        print ""
        print "DRIFT CORRECTION: Active (using velocity feedback)"
        print "="*60
        print ""
        print "Current Throttle: %d%% (PWM: %d)" % (current_percent, current_pwm)
        print ""

        # Set terminal to cbreak mode for the interactive loop
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(sys.stdin.fileno())

            last_override_time = time.time()

            while True:
                # Get current velocity for drift correction
                vx, vy = get_velocity(master)

                if vx is not None and vy is not None:
                    # Calculate corrections (negative feedback)
                    roll_correction = int(KP_ROLL * vy)    # vy is left/right velocity (sign flipped)
                    pitch_correction = int(KP_PITCH * vx)  # vx is forward/back velocity (sign flipped)

                    # Limit corrections to prevent excessive tilting
                    roll_correction = max(-MAX_CORRECTION, min(MAX_CORRECTION, roll_correction))
                    pitch_correction = max(-MAX_CORRECTION, min(MAX_CORRECTION, pitch_correction))

                    # Apply corrections to roll and pitch channels
                    rc_channels[0] = NEUTRAL + roll_correction
                    rc_channels[1] = NEUTRAL + pitch_correction

                    # Debug output every 20 iterations (~1 second)
                    if hasattr(interactive_throttle, 'debug_counter'):
                        interactive_throttle.debug_counter += 1
                    else:
                        interactive_throttle.debug_counter = 0

                    if interactive_throttle.debug_counter % 50 == 0:
                        print "[DRIFT] vx=%.2f vy=%.2f | Roll=%d Pitch=%d" % (vx, vy, roll_correction, pitch_correction)
                else:
                    # No velocity data, use neutral
                    rc_channels[0] = NEUTRAL
                    rc_channels[1] = NEUTRAL

                # Keep sending RC override every 100ms to maintain control
                if time.time() - last_override_time > 0.1:
                    set_rc_override(master, rc_channels)
                    last_override_time = time.time()

                # Check for keyboard input (non-blocking with timeout)
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    ch = sys.stdin.read(1)

                    # Handle arrow keys (they send 3 characters: ESC [ A/B)
                    if ch == '\x1b':  # ESC
                        # Read next 2 characters
                        ch2 = sys.stdin.read(1)
                        if ch2 == '[':
                            ch3 = sys.stdin.read(1)

                            # UP arrow
                            if ch3 == 'A':
                                if current_percent + STEP <= MAX_PERCENT:
                                    # Update to new value
                                    current_percent += STEP
                                    current_pwm = pwm_from_percent(current_percent)
                                    print "Throttle: %d%% (PWM: %d)" % (current_percent, current_pwm)

                                    # Set new throttle
                                    rc_channels[2] = current_pwm
                                    set_rc_override(master, rc_channels)
                                    last_override_time = time.time()
                                else:
                                    print "MAX throttle reached (100%%)!"

                            # DOWN arrow
                            elif ch3 == 'B':
                                if current_percent - STEP >= MIN_PERCENT:
                                    # Update to new value
                                    current_percent -= STEP
                                    current_pwm = pwm_from_percent(current_percent)
                                    print "Throttle: %d%% (PWM: %d)" % (current_percent, current_pwm)

                                    # Set new throttle
                                    rc_channels[2] = current_pwm
                                    set_rc_override(master, rc_channels)
                                    last_override_time = time.time()
                                else:
                                    print "MIN throttle reached (0%%)!"

                    # Exit on 'x'
                    elif ch == 'x' or ch == 'X':
                        print "\n\nExiting..."
                        break

                # Control loop rate (50Hz for responsive drift correction)
                time.sleep(0.02)

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        # Cleanup
        print "Stopping all motors..."
        rc_channels[2] = THROTTLE_MIN
        set_rc_override(master, rc_channels)
        time.sleep(0.5)

        print "Releasing RC override..."
        release_rc_override(master)
        time.sleep(0.5)

        # Disarm
        disarm_throttle(master)

        print "\n" + "="*60
        print "SESSION COMPLETE"
        print "Final throttle tested: %d%% (PWM: %d)" % (current_percent, current_pwm)
        print "="*60

    except KeyboardInterrupt:
        print "\n\nEMERGENCY STOP!"
        if master:
            release_rc_override(master)
            disarm_throttle(master)

    except Exception as e:
        print "\nERROR: %s" % str(e)
        import traceback
        traceback.print_exc()
        if master:
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


if __name__ == "__main__":
    interactive_throttle()
