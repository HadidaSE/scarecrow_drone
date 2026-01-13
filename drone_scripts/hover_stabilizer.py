#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Simple Hover Stabilization - Pure IMU Control
Goal: Start with equal motor power, maintain level attitude (0,0,0)

This script implements a basic flight controller that:
1. Reads IMU data (Roll, Pitch, Yaw)
2. Calibrates starting position as reference (0,0,0)
3. Uses PID controllers to maintain level attitude
4. Directly controls motor PWM values based on corrections
"""

from pymavlink import mavutil
import time
import math
import sys
import tty
import termios
import select

class HoverStabilizer:
    def __init__(self):
        self.master = None

        # Target attitude (all zeros = level)
        self.target_roll = 0.0
        self.target_pitch = 0.0
        self.target_yaw_rate = 0.0  # Don't rotate

        # Reference calibration (set on startup)
        self.reference_roll = 0.0
        self.reference_pitch = 0.0
        self.reference_yaw = 0.0

        # Throttle control (adjustable with UP/DOWN arrows)
        self.current_throttle = 1350  # Starting throttle
        self.THROTTLE_STEP = 10       # PWM change per keypress
        self.THROTTLE_MIN = 1000      # Minimum PWM
        self.THROTTLE_MAX = 2000      # Maximum PWM

        # PID gains for Roll (TUNE THESE!)
        self.KP_ROLL = 2.0    # Proportional: responsiveness to error
        self.KI_ROLL = 0.1    # Integral: eliminates steady-state error
        self.KD_ROLL = 0.5    # Derivative: dampens oscillations

        # PID gains for Pitch
        self.KP_PITCH = 2.0
        self.KI_PITCH = 0.1
        self.KD_PITCH = 0.5

        # PID gains for Yaw rate
        self.KP_YAW = 3.0
        self.KI_YAW = 0.05
        self.KD_YAW = 0.2

        # PID state variables
        self.roll_integral = 0.0
        self.pitch_integral = 0.0
        self.yaw_integral = 0.0

        self.last_roll_error = 0.0
        self.last_pitch_error = 0.0
        self.last_yaw_error = 0.0

        self.last_time = time.time()

        # Limits
        self.MAX_INTEGRAL = 50.0      # Prevent integral windup
        self.MAX_CORRECTION = 300     # Max PWM correction per axis
        self.PWM_MIN = 1000
        self.PWM_MAX = 2000

    def connect(self):
        """Connect to flight controller"""
        print "Connecting to flight controller on /dev/ttyS1..."
        self.master = mavutil.mavlink_connection('/dev/ttyS1', baud=1500000)
        self.master.wait_heartbeat()
        print "Connected! System %u Component %u" % (self.master.target_system, self.master.target_component)

        # Request IMU data at high rate
        print "Requesting ATTITUDE stream at 50 Hz..."
        self.master.mav.request_data_stream_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_EXTRA1,
            50,  # 50 Hz
            1    # Start
        )

        # Also request servo outputs for monitoring
        self.master.mav.request_data_stream_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS,
            10,  # 10 Hz
            1
        )

        time.sleep(1)

    def set_mode(self, mode):
        """Set flight mode"""
        mode_mapping = self.master.mode_mapping()
        if mode not in mode_mapping:
            print "Unknown mode: %s" % mode
            print "Available modes:", mode_mapping.keys()
            return False

        mode_id = mode_mapping[mode]
        if isinstance(mode_id, tuple):
            mode_id = mode_id[0]
        mode_id = int(mode_id)

        self.master.mav.set_mode_send(
            self.master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
        print "Mode set to %s" % mode
        return True

    def arm_motors(self):
        """Arm the drone"""
        print "Arming motors..."
        self.master.arducopter_arm()
        self.master.motors_armed_wait()
        print "ARMED!"

    def disarm_motors(self):
        """Disarm the drone"""
        print "Disarming motors..."
        self.master.arducopter_disarm()
        self.master.motors_disarmed_wait()
        print "DISARMED"

    def calibrate_zero_reference(self):
        """
        Read IMU and set current attitude as zero reference
        This makes the starting position = level (0, 0, 0)
        """
        print "\nCalibrating zero reference..."
        print "Make sure drone is on level ground!"
        time.sleep(1)

        samples = []
        for i in range(50):  # Collect 50 samples (~1 second)
            msg = self.master.recv_match(type='ATTITUDE', blocking=True, timeout=1)
            if msg:
                samples.append({
                    'roll': math.degrees(msg.roll),
                    'pitch': math.degrees(msg.pitch),
                    'yaw': math.degrees(msg.yaw)
                })
            time.sleep(0.02)

        if len(samples) > 0:
            # Average the samples
            self.reference_roll = sum(s['roll'] for s in samples) / len(samples)
            self.reference_pitch = sum(s['pitch'] for s in samples) / len(samples)
            self.reference_yaw = sum(s['yaw'] for s in samples) / len(samples)

            print "CALIBRATION COMPLETE!"
            print "  Reference Roll:  %.2f deg (will be treated as 0)" % self.reference_roll
            print "  Reference Pitch: %.2f deg (will be treated as 0)" % self.reference_pitch
            print "  Reference Yaw:   %.2f deg (will be treated as 0)" % self.reference_yaw
        else:
            print "WARNING: Could not calibrate! Using 0, 0, 0"
            self.reference_roll = 0.0
            self.reference_pitch = 0.0
            self.reference_yaw = 0.0

    def get_imu_data(self):
        """Read current IMU attitude"""
        msg = self.master.recv_match(type='ATTITUDE', blocking=False)
        if msg:
            return {
                'roll': math.degrees(msg.roll),
                'pitch': math.degrees(msg.pitch),
                'yaw': math.degrees(msg.yaw),
                'rollspeed': math.degrees(msg.rollspeed),
                'pitchspeed': math.degrees(msg.pitchspeed),
                'yawspeed': math.degrees(msg.yawspeed),
            }
        return None

    def pid_update(self, target, current, rate, integral, last_error, kp, ki, kd, dt):
        """
        PID controller update

        Args:
            target: Desired value
            current: Current value
            rate: Current rate of change (for derivative term)
            integral: Accumulated integral
            last_error: Previous error (for derivative calculation)
            kp, ki, kd: PID gains
            dt: Time delta since last update

        Returns:
            (output, new_integral)
        """
        # Error
        error = target - current

        # Proportional term
        p_term = kp * error

        # Integral term (with anti-windup)
        integral += error * dt
        integral = max(-self.MAX_INTEGRAL, min(self.MAX_INTEGRAL, integral))
        i_term = ki * integral

        # Derivative term (using rate for better performance)
        # We use negative rate because we want to dampen movement
        d_term = -kd * rate

        # Total output
        output = p_term + i_term + d_term

        # Limit output
        output = max(-self.MAX_CORRECTION, min(self.MAX_CORRECTION, output))

        return output, integral

    def motor_mixing(self, roll_correction, pitch_correction, yaw_correction):
        """
        Convert corrections to individual motor PWM values

        Quad-X configuration:
            FRONT
          M1     M2
            \ + /
            / + \
          M3     M4
            BACK

        M1 = Front-Left (CCW)
        M2 = Front-Right (CW)
        M3 = Back-Left (CW)
        M4 = Back-Right (CCW)

        Mixing logic:
        - Roll correction: increases right motors, decreases left motors
        - Pitch correction: increases back motors, decreases front motors
        - Yaw correction: increases CW motors, decreases CCW motors
        """
        # Start with current throttle (adjustable with UP/DOWN arrows)
        base = self.current_throttle

        # Apply corrections based on motor positions
        m1 = base - pitch_correction - roll_correction - yaw_correction
        m2 = base - pitch_correction + roll_correction + yaw_correction
        m3 = base + pitch_correction - roll_correction + yaw_correction
        m4 = base + pitch_correction + roll_correction - yaw_correction

        # Limit all motor values to safe range
        motors = [m1, m2, m3, m4]
        motors = [max(self.PWM_MIN, min(self.PWM_MAX, int(m))) for m in motors]

        return motors

    def send_motor_commands(self, motor_pwms):
        """
        Send PWM commands directly to motors

        In MANUAL mode with direct servo configuration (from configure_direct_control.py),
        RC channels map directly to servos/motors:
        - RC Channel 1 -> Servo 1 -> Motor 1
        - RC Channel 2 -> Servo 2 -> Motor 2
        - RC Channel 3 -> Servo 3 -> Motor 3
        - RC Channel 4 -> Servo 4 -> Motor 4

        Your PWM values go DIRECTLY to ESCs with NO ArduPilot processing!
        """
        self.master.mav.rc_channels_override_send(
            self.master.target_system,
            self.master.target_component,
            motor_pwms[0],  # Channel 1 -> Motor 1 (PWM direct)
            motor_pwms[1],  # Channel 2 -> Motor 2 (PWM direct)
            motor_pwms[2],  # Channel 3 -> Motor 3 (PWM direct)
            motor_pwms[3],  # Channel 4 -> Motor 4 (PWM direct)
            0, 0, 0, 0      # Channels 5-8 unused
        )

    def release_rc_override(self):
        """Release RC override control"""
        self.master.mav.rc_channels_override_send(
            self.master.target_system,
            self.master.target_component,
            0, 0, 0, 0, 0, 0, 0, 0
        )

    def get_motor_outputs(self):
        """Read actual motor outputs for monitoring"""
        msg = self.master.recv_match(type='SERVO_OUTPUT_RAW', blocking=False)
        if msg:
            return [msg.servo1_raw, msg.servo2_raw, msg.servo3_raw, msg.servo4_raw]
        return None

    def run(self):
        """Main stabilization loop with keyboard control"""
        print "\n" + "="*70
        print "HOVER STABILIZATION - FULL MOTOR CONTROL"
        print "="*70
        print ""
        print "This script gives you 100% control over motor PWM."
        print "ArduPilot stabilization is DISABLED."
        print "YOU are the flight controller!"
        print ""
        print "Target: Maintain level attitude (0, 0, 0)"
        print "Starting throttle: %d PWM (adjustable with UP/DOWN)" % self.current_throttle
        print ""
        print "CONTROLS:"
        print "  UP/DOWN Arrows = Increase/Decrease throttle"
        print "  X = Stop motors and exit"
        print ""

        # Setup flight controller for direct control
        print "Setting MANUAL mode (direct motor control)..."
        self.set_mode('MANUAL')
        time.sleep(1)

        print "Arming motors..."
        self.arm_motors()
        time.sleep(1)

        print "\nMotors armed and ready!"
        print "Starting stabilization in 2 seconds..."
        print "Control loop will run at 50 Hz"
        print ""
        time.sleep(2)

        loop_hz = 50
        loop_period = 1.0 / loop_hz

        iteration = 0

        # Set terminal to cbreak mode for keyboard input
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(sys.stdin.fileno())

            while True:
                loop_start = time.time()

                # 1. Read IMU
                imu = self.get_imu_data()

                if imu:
                    # 2. Calculate time delta
                    current_time = time.time()
                    dt = current_time - self.last_time
                    self.last_time = current_time

                    if dt <= 0 or dt > 1.0:  # Sanity check
                        dt = loop_period

                    # 3. Normalize attitude relative to reference (make reference = 0)
                    roll = imu['roll'] - self.reference_roll
                    pitch = imu['pitch'] - self.reference_pitch
                    yaw_rate = imu['yawspeed']  # We control rate, not absolute yaw

                    # 4. Run PID controllers for each axis
                    roll_correction, self.roll_integral = self.pid_update(
                        self.target_roll, roll, imu['rollspeed'],
                        self.roll_integral, self.last_roll_error,
                        self.KP_ROLL, self.KI_ROLL, self.KD_ROLL, dt
                    )

                    pitch_correction, self.pitch_integral = self.pid_update(
                        self.target_pitch, pitch, imu['pitchspeed'],
                        self.pitch_integral, self.last_pitch_error,
                        self.KP_PITCH, self.KI_PITCH, self.KD_PITCH, dt
                    )

                    yaw_correction, self.yaw_integral = self.pid_update(
                        self.target_yaw_rate, yaw_rate, 0,  # No derivative for rate control
                        self.yaw_integral, self.last_yaw_error,
                        self.KP_YAW, self.KI_YAW, self.KD_YAW, dt
                    )

                    # 5. Motor mixing - convert corrections to individual motor PWMs
                    motor_pwms = self.motor_mixing(roll_correction, pitch_correction, yaw_correction)

                    # 6. Send commands to motors
                    self.send_motor_commands(motor_pwms)

                    # 7. Display status (every 10 iterations = 5 Hz display rate)
                    iteration += 1
                    if iteration % 10 == 0:
                        actual_motors = self.get_motor_outputs()
                        print "\n" + "="*70
                        print "THROTTLE: %d PWM (UP/DOWN to adjust)" % self.current_throttle
                        print "IMU: Roll=%+6.2f° Pitch=%+6.2f° YawRate=%+6.2f°/s" % (roll, pitch, yaw_rate)
                        print "PID: Roll=%+6.1f  Pitch=%+6.1f  Yaw=%+6.1f" % (
                            roll_correction, pitch_correction, yaw_correction
                        )
                        print "CMD: M1=%4d  M2=%4d  M3=%4d  M4=%4d" % tuple(motor_pwms)
                        if actual_motors:
                            print "ACT: M1=%4d  M2=%4d  M3=%4d  M4=%4d" % tuple(actual_motors)
                            spread = max(actual_motors) - min(actual_motors)
                            print "     Spread=%d PWM" % spread
                        print "="*70

                # Check for keyboard input (non-blocking)
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
                                if self.current_throttle + self.THROTTLE_STEP <= self.THROTTLE_MAX:
                                    self.current_throttle += self.THROTTLE_STEP
                                    print "\nThrottle: %d PWM (increased)" % self.current_throttle
                                else:
                                    print "\nMAX throttle! (%d PWM)" % self.THROTTLE_MAX

                            # DOWN arrow - Decrease throttle
                            elif ch3 == 'B':
                                if self.current_throttle - self.THROTTLE_STEP >= self.THROTTLE_MIN:
                                    self.current_throttle -= self.THROTTLE_STEP
                                    print "\nThrottle: %d PWM (decreased)" % self.current_throttle
                                else:
                                    print "\nMIN throttle! (%d PWM)" % self.THROTTLE_MIN

                    # Exit on 'x' or 'X'
                    elif ch == 'x' or ch == 'X':
                        print "\n\nExiting..."
                        break

                # Maintain loop rate
                elapsed = time.time() - loop_start
                if elapsed < loop_period:
                    time.sleep(loop_period - elapsed)

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            # Stop all motors
            print "Stopping all motors..."
            self.send_motor_commands([1000, 1000, 1000, 1000])
            time.sleep(0.5)

            # Release RC override
            print "Releasing RC override..."
            self.release_rc_override()
            time.sleep(0.5)

            # Disarm
            print "Disarming..."
            self.disarm_motors()

            print "Motors stopped and disarmed"


def main():
    print "="*70
    print "HOVER STABILIZATION SYSTEM - FULL MOTOR CONTROL"
    print "="*70
    print ""
    print "IMPORTANT: Before running this script for the first time:"
    print "  1. Run: python configure_direct_control.py"
    print "  2. Reboot the drone"
    print "  3. Then run this script"
    print ""
    print "This script gives you 100% control over motors:"
    print "  - Reads IMU values (Roll, Pitch, Yaw)"
    print "  - Calibrates starting position as reference (0,0,0)"
    print "  - Calculates PID corrections based on tilt"
    print "  - Adjustable throttle with UP/DOWN arrows (starts at 1250 PWM)"
    print "  - Sends PWM DIRECTLY to motors (no ArduPilot processing)"
    print ""
    print "YOU are the flight controller!"
    print "ArduPilot only passes through your commands."
    print ""
    print "WARNING: Remove propellers for first test!"
    print ""

    raw_input("Press ENTER to start (Ctrl+C to cancel)...")
    print ""

    # Create stabilizer instance
    stabilizer = HoverStabilizer()

    # Connect to flight controller
    stabilizer.connect()

    # Calibrate zero reference point
    stabilizer.calibrate_zero_reference()

    print "\nReady to start!"
    print "\nNOTE: You may need to adjust base_throttle in the code"
    print "      Start low and increase gradually until drone hovers"
    print ""
    raw_input("Press ENTER to begin stabilization...")

    # Run main control loop
    stabilizer.run()


if __name__ == "__main__":
    main()
