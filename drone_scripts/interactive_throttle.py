#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Interactive Throttle Control with IMU Monitoring & Manual Trim - Intel Aero RTF Drone
IMU-only flight (STABILIZE mode) with real-time motor PWM and attitude display
No GPS/EKF required - works immediately with gyro + accelerometer only

Features:
  - Real-time IMU attitude display (roll, pitch, yaw in degrees)
  - Real-time motor PWM outputs (all 4-8 motors)
  - Manual trim controls to counteract drift
  - Interactive throttle control

Controls:
  UP/DOWN arrows: Adjust throttle PWM
  LEFT/RIGHT arrows: Adjust roll trim (counteract left/right drift)
  W/S keys: Adjust pitch trim (counteract forward/backward drift)
  X: Exit
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


def request_servo_stream(master):
    """Request servo output and attitude data streams"""
    print "Requesting motor output and attitude streams..."

    # Request RC_CHANNELS stream (includes SERVO_OUTPUT_RAW)
    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS,
        10,  # 10 Hz
        1    # Start streaming
    )

    # Request EXTRA1 stream (includes ATTITUDE)
    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_EXTRA1,
        10,  # 10 Hz
        1    # Start streaming
    )

    # Request EXTRA2 stream (also may include ATTITUDE)
    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_EXTRA2,
        10,  # 10 Hz
        1    # Start streaming
    )

    print "Data streams requested"


def get_motor_outputs(master):
    """Get actual motor PWM outputs from SERVO_OUTPUT_RAW"""
    # Cache last known motor outputs
    if not hasattr(get_motor_outputs, 'last_motors'):
        get_motor_outputs.last_motors = None

    try:
        # Check for new messages (non-blocking)
        msg = master.recv_match(type='SERVO_OUTPUT_RAW', blocking=False)
        if msg:
            motors = {
                'motor1': msg.servo1_raw,
                'motor2': msg.servo2_raw,
                'motor3': msg.servo3_raw,
                'motor4': msg.servo4_raw,
                'motor5': msg.servo5_raw,
                'motor6': msg.servo6_raw,
                'motor7': msg.servo7_raw,
                'motor8': msg.servo8_raw,
            }
            get_motor_outputs.last_motors = motors
            return motors
    except:
        pass

    # Return last known values if available
    return get_motor_outputs.last_motors


def get_attitude(master):
    """Get attitude (roll, pitch, yaw) from IMU"""
    # Cache last known attitude
    if not hasattr(get_attitude, 'last_attitude'):
        get_attitude.last_attitude = None

    try:
        msg = master.recv_match(type='ATTITUDE', blocking=False)
        if msg:
            import math
            attitude = {
                'roll': math.degrees(msg.roll),    # Convert radians to degrees
                'pitch': math.degrees(msg.pitch),
                'yaw': math.degrees(msg.yaw),
                'rollspeed': math.degrees(msg.rollspeed),
                'pitchspeed': math.degrees(msg.pitchspeed),
                'yawspeed': math.degrees(msg.yawspeed),
            }
            get_attitude.last_attitude = attitude
            return attitude
    except:
        pass

    return get_attitude.last_attitude


def interactive_throttle():
    """
    Interactive throttle control with motor monitoring and manual trim
    """
    # Throttle PWM values (1000 = motors off, 2000 = full throttle)
    current_throttle_pwm = 1450  # Starting throttle (motors will spin)
    THROTTLE_STEP = 10            # PWM change per keypress
    THROTTLE_MIN = 1000          # Minimum PWM
    THROTTLE_MAX = 2000          # Maximum PWM

    # Manual trim values (adjust to counteract drift)
    roll_trim = 0                 # Manual roll trim (-100 to +100)
    pitch_trim = 0                # Manual pitch trim (-100 to +100)
    TRIM_STEP = 5                 # Trim change per keypress
    MAX_TRIM = 200                # Maximum trim value

    # Attitude reference calibration (set current attitude as "level")
    reference_roll = None         # Calibrated roll reference
    reference_pitch = None        # Calibrated pitch reference
    auto_correct_enabled = False  # Auto-correction based on attitude

    # Auto-correction gains
    KP_ROLL_ATTITUDE = 10         # PWM correction per degree of roll
    KP_PITCH_ATTITUDE = 10        # PWM correction per degree of pitch

    NEUTRAL = 1500

    print "="*60
    print "MOTOR MONITORING - INTEL AERO (IMU-ONLY/STABILIZE)"
    print "="*60
    print ""
    print "Mode: STABILIZE (gyro + accelerometer only)"
    print "No GPS/EKF required - works immediately"
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

        # Request motor output stream
        request_servo_stream(master)
        time.sleep(1)

        # Set mode to STABILIZED
        set_mode(master, 'STABILIZED')
        time.sleep(1)

        # Arm throttle
        arm_throttle(master)
        time.sleep(1)

        # AUTO-CALIBRATE: Read current attitude before motors start
        print "\nAuto-calibrating level reference..."
        time.sleep(0.5)  # Wait for attitude data

        # Read current attitude several times to get stable reading
        for i in range(10):
            attitude = get_attitude(master)
            time.sleep(0.05)

        if attitude:
            reference_roll = attitude['roll']
            reference_pitch = attitude['pitch']
            auto_correct_enabled = True  # Enable auto-correction by default
            print "CALIBRATED! Current attitude set as level reference:"
            print "  Roll=%.1f deg | Pitch=%.1f deg" % (reference_roll, reference_pitch)
            print "  Auto-correction ENABLED"
            print "  Motors will maintain this attitude as 'level'"
        else:
            print "WARNING: Could not read attitude for auto-calibration"
            print "  Proceeding without auto-correction"

        time.sleep(1)

        # Set initial throttle
        rc_channels = [NEUTRAL, NEUTRAL, current_throttle_pwm, NEUTRAL, 0, 0, 0, 0]
        set_rc_override(master, rc_channels)
        time.sleep(0.5)

        # Interactive control
        print "\n" + "="*60
        print "CONTROLS:"
        print "  UP/DOWN Arrows    = Increase/Decrease throttle"
        print "  LEFT/RIGHT Arrows = Manual roll trim"
        print "  W/S Keys          = Manual pitch trim"
        print "  C                 = Calibrate current attitude as 'level' (0,0)"
        print "  A                 = Toggle auto-correction ON/OFF"
        print "  X                 = Stop motors and exit"
        print ""
        print "Mode: STABILIZED (IMU-only, no GPS needed)"
        print "Auto-correction: Adjusts motors to maintain calibrated level"
        print "="*60
        print ""

        # Set terminal to cbreak mode for the interactive loop
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(sys.stdin.fileno())

            last_override_time = time.time()
            display_counter = 0

            while True:
                # Get motor outputs and attitude
                motors = get_motor_outputs(master)
                attitude = get_attitude(master)

                # Calculate auto-corrections based on attitude deviation
                auto_roll_correction = 0
                auto_pitch_correction = 0

                if auto_correct_enabled and attitude and reference_roll is not None:
                    # Base offset: Tell flight controller to maintain the calibrated tilt (not level to 0)
                    # This counteracts STABILIZE mode's attempt to level the drone
                    base_roll_offset = int(KP_ROLL_ATTITUDE * reference_roll)
                    base_pitch_offset = int(KP_PITCH_ATTITUDE * reference_pitch)

                    # Deviation correction: Return to reference if attitude changes
                    roll_error = attitude['roll'] - reference_roll
                    pitch_error = attitude['pitch'] - reference_pitch

                    deviation_roll_correction = int(-KP_ROLL_ATTITUDE * roll_error)
                    deviation_pitch_correction = int(-KP_PITCH_ATTITUDE * pitch_error)

                    # Total correction = base offset + deviation correction
                    auto_roll_correction = base_roll_offset + deviation_roll_correction
                    auto_pitch_correction = base_pitch_offset + deviation_pitch_correction

                    # Limit corrections
                    auto_roll_correction = max(-MAX_TRIM, min(MAX_TRIM, auto_roll_correction))
                    auto_pitch_correction = max(-MAX_TRIM, min(MAX_TRIM, auto_pitch_correction))

                # Apply trim + auto-corrections to RC channels
                rc_channels[0] = NEUTRAL + roll_trim + auto_roll_correction
                rc_channels[1] = NEUTRAL + pitch_trim + auto_pitch_correction

                # Display every 10 iterations (~0.2 second at 50Hz loop)
                display_counter += 1
                if display_counter % 10 == 0:
                    print ""
                    print "="*70

                    # Display attitude from IMU
                    if attitude:
                        print "IMU ATTITUDE: Roll=%.1f deg | Pitch=%.1f deg | Yaw=%.1f deg" % (
                            attitude['roll'], attitude['pitch'], attitude['yaw'])
                    else:
                        print "IMU ATTITUDE: Waiting for data..."

                    # Display reference attitude and auto-correction status
                    if reference_roll is not None:
                        print "REFERENCE: Roll=%.1f deg | Pitch=%.1f deg (calibrated level)" % (
                            reference_roll, reference_pitch)
                        if auto_correct_enabled:
                            print "AUTO-CORRECTION: ON | Roll=%+d PWM | Pitch=%+d PWM" % (
                                auto_roll_correction, auto_pitch_correction)
                        else:
                            print "AUTO-CORRECTION: OFF (press A to enable)"
                    else:
                        print "AUTO-CORRECTION: Not calibrated (press C to calibrate)"

                    # Display manual trim values
                    print "MANUAL TRIM: Roll=%+d | Pitch=%+d" % (roll_trim, pitch_trim)

                    # Display commands
                    print "THROTTLE: %d PWM" % current_throttle_pwm
                    print "RC CHANNELS: Roll=%d | Pitch=%d | Throttle=%d | Yaw=%d" % (
                        rc_channels[0], rc_channels[1], rc_channels[2], rc_channels[3])

                    # Display motor outputs
                    if motors:
                        print "MOTOR OUTPUTS:"
                        print "  M1=%d  M2=%d  M3=%d  M4=%d" % (
                            motors['motor1'], motors['motor2'], motors['motor3'], motors['motor4'])
                        if motors['motor5'] > 0 or motors['motor6'] > 0:
                            print "  M5=%d  M6=%d  M7=%d  M8=%d" % (
                                motors['motor5'], motors['motor6'], motors['motor7'], motors['motor8'])
                    else:
                        print "MOTOR OUTPUTS: Waiting for data..."
                    print "="*70

                # Keep sending RC override every 100ms to maintain control
                if time.time() - last_override_time > 0.1:
                    set_rc_override(master, rc_channels)
                    last_override_time = time.time()

                # Check for keyboard input (non-blocking with timeout)
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    ch = sys.stdin.read(1)

                    # Handle arrow keys (they send 3 characters: ESC [ A/B/C/D)
                    if ch == '\x1b':  # ESC
                        # Read next 2 characters
                        ch2 = sys.stdin.read(1)
                        if ch2 == '[':
                            ch3 = sys.stdin.read(1)

                            # UP arrow - Increase throttle
                            if ch3 == 'A':
                                if current_throttle_pwm + THROTTLE_STEP <= THROTTLE_MAX:
                                    current_throttle_pwm += THROTTLE_STEP
                                    print "Throttle: %d PWM" % current_throttle_pwm
                                    rc_channels[2] = current_throttle_pwm
                                else:
                                    print "MAX throttle!"

                            # DOWN arrow - Decrease throttle
                            elif ch3 == 'B':
                                if current_throttle_pwm - THROTTLE_STEP >= THROTTLE_MIN:
                                    current_throttle_pwm -= THROTTLE_STEP
                                    print "Throttle: %d PWM" % current_throttle_pwm
                                    rc_channels[2] = current_throttle_pwm
                                else:
                                    print "MIN throttle!"

                            # RIGHT arrow - Increase roll trim (tilt right to counteract left drift)
                            elif ch3 == 'C':
                                if roll_trim + TRIM_STEP <= MAX_TRIM:
                                    roll_trim += TRIM_STEP
                                    print "Roll trim: %+d (tilting right)" % roll_trim
                                else:
                                    print "MAX roll trim!"

                            # LEFT arrow - Decrease roll trim (tilt left to counteract right drift)
                            elif ch3 == 'D':
                                if roll_trim - TRIM_STEP >= -MAX_TRIM:
                                    roll_trim -= TRIM_STEP
                                    print "Roll trim: %+d (tilting left)" % roll_trim
                                else:
                                    print "MAX roll trim!"

                    # W key - Increase pitch trim (tilt forward to counteract backward drift)
                    elif ch == 'w' or ch == 'W':
                        if pitch_trim + TRIM_STEP <= MAX_TRIM:
                            pitch_trim += TRIM_STEP
                            print "Pitch trim: %+d (tilting forward)" % pitch_trim
                        else:
                            print "MAX pitch trim!"

                    # S key - Decrease pitch trim (tilt backward to counteract forward drift)
                    elif ch == 's' or ch == 'S':
                        if pitch_trim - TRIM_STEP >= -MAX_TRIM:
                            pitch_trim -= TRIM_STEP
                            print "Pitch trim: %+d (tilting backward)" % pitch_trim
                        else:
                            print "MAX pitch trim!"

                    # C key - Calibrate current attitude as level reference
                    elif ch == 'c' or ch == 'C':
                        if attitude:
                            reference_roll = attitude['roll']
                            reference_pitch = attitude['pitch']
                            print "CALIBRATED! Level reference set:"
                            print "  Roll=%.1f deg | Pitch=%.1f deg" % (reference_roll, reference_pitch)
                            print "Press A to enable auto-correction"
                        else:
                            print "Cannot calibrate - no attitude data!"

                    # A key - Toggle auto-correction on/off
                    elif ch == 'a' or ch == 'A':
                        if reference_roll is not None:
                            auto_correct_enabled = not auto_correct_enabled
                            if auto_correct_enabled:
                                print "AUTO-CORRECTION: ENABLED"
                                print "  Will maintain calibrated level attitude"
                            else:
                                print "AUTO-CORRECTION: DISABLED"
                        else:
                            print "Cannot enable auto-correction - not calibrated!"
                            print "Press C first to calibrate level"

                    # Exit on 'x'
                    elif ch == 'x' or ch == 'X':
                        print "\n\nExiting..."
                        break

                # Control loop rate (50Hz)
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

        print "\n" + "="*70
        print "SESSION COMPLETE"
        print "Final throttle PWM: %d" % current_throttle_pwm
        print "Final trim - Roll: %+d | Pitch: %+d" % (roll_trim, pitch_trim)
        print "="*70

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
