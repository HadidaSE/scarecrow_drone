#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Simple Hover Stabilization - Pure IMU Control (PX4 Version)
Goal: Start with equal motor power, maintain level attitude (0,0,0)

This script implements a basic flight controller for PX4 that:
1. Reads IMU data (Roll, Pitch, Yaw)
2. Calibrates starting position as reference (0,0,0)
3. Uses PID controllers to maintain level attitude
4. Directly controls motors using OFFBOARD mode and actuator commands

PX4 OFFBOARD MODE:
- Uses SET_ACTUATOR_CONTROL_TARGET for direct motor control
- Bypasses PX4's attitude/position controllers
- Requires constant messages (>2Hz) or switches to failsafe
"""

from pymavlink import mavutil
import time
import math
import sys
import tty
import termios
import select

class HoverStabilizerPX4:
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

        # Throttle control (0.0 to 1.0 normalized)
        self.current_throttle = 0.25  # Starting throttle (25%)
        self.THROTTLE_STEP = 0.01     # 1% change per keypress
        self.THROTTLE_MIN = 0.0       # 0%
        self.THROTTLE_MAX = 0.8       # 80% max for safety

        # PID gains for Roll (TUNE THESE!)
        self.KP_ROLL = 0.5    # Proportional: responsiveness to error
        self.KI_ROLL = 0.02   # Integral: eliminates steady-state error
        self.KD_ROLL = 0.1    # Derivative: dampens oscillations

        # PID gains for Pitch
        self.KP_PITCH = 0.5
        self.KI_PITCH = 0.02
        self.KD_PITCH = 0.1

        # PID gains for Yaw rate
        self.KP_YAW = 0.3
        self.KI_YAW = 0.01
        self.KD_YAW = 0.05

        # PID state variables
        self.roll_integral = 0.0
        self.pitch_integral = 0.0
        self.yaw_integral = 0.0

        self.last_roll_error = 0.0
        self.last_pitch_error = 0.0
        self.last_yaw_error = 0.0

        self.last_time = time.time()

        # Limits
        self.MAX_INTEGRAL = 0.5       # Prevent integral windup
        self.MAX_CORRECTION = 0.3     # Max correction per axis (normalized)

        # OFFBOARD heartbeat
        self.last_offboard_time = 0
        self.offboard_interval = 0.05  # 20 Hz

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

    def set_offboard_mode(self):
        """
        Set MANUAL mode for direct RC control
        MANUAL mode with low PX4 gains = minimal interference
        """
        print "Setting ACRO mode..."

        # Set ACRO mode (PX4 custom mode 2)
        self.master.mav.set_mode_send(
            self.master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            2  # ACRO mode ID for PX4
        )

        time.sleep(1)
        print "ACRO mode set - RC override active"

    def arm_motors(self):
        """Arm the drone"""
        print "Arming motors..."

        # PX4 arming command
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # confirmation
            1,  # param1: 1 to arm
            0, 0, 0, 0, 0, 0
        )

        # Wait for arm confirmation
        time.sleep(2)
        print "ARMED!"

    def disarm_motors(self):
        """Disarm the drone"""
        print "Disarming motors..."

        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # confirmation
            0,  # param1: 0 to disarm
            0, 0, 0, 0, 0, 0
        )

        time.sleep(1)
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

        Returns normalized output (-1 to 1) for actuator control
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
        d_term = -kd * rate

        # Total output
        output = p_term + i_term + d_term

        # Limit output to -1 to 1
        output = max(-self.MAX_CORRECTION, min(self.MAX_CORRECTION, output))

        return output, integral

    def motor_mixing(self, roll_correction, pitch_correction, yaw_correction):
        """
        Convert corrections to individual motor values (normalized 0-1)

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
        """
        base = self.current_throttle

        # Apply corrections based on motor positions
        m1 = base - pitch_correction - roll_correction - yaw_correction
        m2 = base - pitch_correction + roll_correction + yaw_correction
        m3 = base + pitch_correction - roll_correction + yaw_correction
        m4 = base + pitch_correction + roll_correction - yaw_correction

        # Limit all motor values to safe range (0-1)
        motors = [m1, m2, m3, m4]
        motors = [max(0.0, min(1.0, m)) for m in motors]

        return motors

    def send_actuator_commands(self, controls):
        """
        Send actuator control commands in OFFBOARD mode

        controls: list of 8 normalized values (-1 to 1)
        For direct motor control:
        - controls[0-3]: motors 1-4 (0-1 range)
        - controls[4-7]: unused

        PX4 group 0 (motors): controls[3] is collective thrust, controls[0-2] are roll/pitch/yaw
        But for direct motor control we use group 1 (actuator_controls_1)
        """
        # Use group 1 for direct actuator output (bypasses mixer mostly)
        # Actually, for quad motors we should use group 0 but with the mixer understanding

        # For PX4, we need to send in the format PX4 expects:
        # Group 0: [roll, pitch, yaw, throttle, ...]
        # The mixer will convert these to individual motor outputs

        # But we want DIRECT motor control, so we'll use the throttle + attitude approach
        # where we send the mixed motor values as roll/pitch/yaw corrections + throttle

        # Convert motor values to control vector
        # This is a workaround - we're sending our computed motor values
        # as attitude + throttle commands

        self.master.mav.set_actuator_control_target_send(
            int(time.time() * 1000000),  # time_usec (microseconds)
            1,  # group (0 = attitude/thrust, 1 = aux outputs)
            self.master.target_system,
            self.master.target_component,
            controls  # 8 float values
        )

    def send_direct_motors(self, motor_values):
        """
        Send motor commands using RC_CHANNELS_OVERRIDE
        
        This sends motor commands as if they're coming from an RC transmitter.
        Works on all PX4 versions including old Intel Aero firmware.
        
        motor_values: [m1, m2, m3, m4] normalized 0-1
        Converts to PWM: 1000-2000 range
        """
        # Convert 0-1 normalized to 1000-2000 PWM
        pwm_values = [int(1000 + (val * 1000)) for val in motor_values]
        
        # Ensure values are in valid range
        pwm_values = [max(1000, min(2000, pwm)) for pwm in pwm_values]
        
        # RC_CHANNELS_OVERRIDE: Send as channels 1-4 (motor outputs in MANUAL mode)
        # Channels: 1=M1, 2=M2, 3=M3, 4=M4
        # Set channels 5-8 to 0 (unchanged)
        self.master.mav.rc_channels_override_send(
            self.master.target_system,
            self.master.target_component,
            pwm_values[0],  # Channel 1 (Motor 1)
            pwm_values[1],  # Channel 2 (Motor 2)
            pwm_values[2],  # Channel 3 (Motor 3)
            pwm_values[3],  # Channel 4 (Motor 4)
            0, 0, 0, 0      # Channels 5-8 (unused)
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
        print "HOVER STABILIZATION - MANUAL MODE RC OVERRIDE"
        print "="*70
        print ""
        print "This script gives you direct motor control via RC override."
        print "Sends PWM values directly to motors (1000-2000)."
        print "YOU are the flight controller!"
        print ""
        print "Target: Maintain level attitude (0, 0, 0)"
        print "Starting throttle: %.1f%% (adjustable with UP/DOWN)" % (self.current_throttle * 100)
        print ""
        print "CONTROLS:"
        print "  UP/DOWN Arrows = Increase/Decrease throttle by 1%%"
        print "  X = Stop motors and exit"
        print ""

        # Setup flight controller for OFFBOARD control
        print "Setting up OFFBOARD mode..."
        self.set_offboard_mode()
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
        
        # Last known motor values (start with equal throttle)
        last_motor_values = [self.current_throttle] * 4

        # Set terminal to cbreak mode for keyboard input
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(sys.stdin.fileno())

            while True:
                loop_start = time.time()

                # 1. Read IMU (non-blocking)
                imu = self.get_imu_data()

                if imu:
                    # 2. Calculate time delta
                    current_time = time.time()
                    dt = current_time - self.last_time
                    self.last_time = current_time

                    if dt <= 0 or dt > 1.0:  # Sanity check
                        dt = loop_period

                    # 3. Normalize attitude relative to reference
                    roll = imu['roll'] - self.reference_roll
                    pitch = imu['pitch'] - self.reference_pitch
                    yaw_rate = imu['yawspeed']

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
                        self.target_yaw_rate, yaw_rate, 0,
                        self.yaw_integral, self.last_yaw_error,
                        self.KP_YAW, self.KI_YAW, self.KD_YAW, dt
                    )

                    # 5. Motor mixing - convert corrections to individual motor values
                    motor_values = self.motor_mixing(roll_correction, pitch_correction, yaw_correction)
                    
                    # Store for next iteration
                    last_motor_values = motor_values

                    # 7. Display status (every 10 iterations = 5 Hz display rate)
                    iteration += 1
                    if iteration % 10 == 0:
                        # Read motor outputs - may be None if no new message
                        actual_motors = self.get_motor_outputs()
                        print "\n" + "="*70
                        print "THROTTLE: %.1f%% (UP/DOWN to adjust)" % (self.current_throttle * 100)
                        print "IMU: Roll=%+6.2f° Pitch=%+6.2f° YawRate=%+6.2f°/s" % (roll, pitch, yaw_rate)
                        print "PID: Roll=%+.3f  Pitch=%+.3f  Yaw=%+.3f" % (
                            roll_correction, pitch_correction, yaw_correction
                        )
                        print "CMD: M1=%.2f  M2=%.2f  M3=%.2f  M4=%.2f (normalized)" % tuple(motor_values)
                        if actual_motors and actual_motors != [0, 0, 0, 0]:
                            print "ACT: M1=%4d  M2=%4d  M3=%4d  M4=%4d (PWM)" % tuple(actual_motors)
                            spread = max(actual_motors) - min(actual_motors)
                            print "     Spread=%d PWM" % spread
                        else:
                            print "ACT: Waiting for SERVO_OUTPUT_RAW..."
                        print "="*70
                
                # 6. CRITICAL: Send motor commands EVERY loop iteration
                # This maintains OFFBOARD mode even if IMU data is delayed
                self.send_direct_motors(last_motor_values)

                # Check for keyboard input (non-blocking)
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    ch = sys.stdin.read(1)

                    # Handle arrow keys
                    if ch == '\x1b':  # ESC
                        ch2 = sys.stdin.read(1)
                        if ch2 == '[':
                            ch3 = sys.stdin.read(1)

                            # UP arrow - Increase throttle
                            if ch3 == 'A':
                                if self.current_throttle + self.THROTTLE_STEP <= self.THROTTLE_MAX:
                                    self.current_throttle += self.THROTTLE_STEP
                                    print "\nThrottle: %.1f%% (increased)" % (self.current_throttle * 100)
                                else:
                                    print "\nMAX throttle! (%.1f%%)" % (self.THROTTLE_MAX * 100)

                            # DOWN arrow - Decrease throttle
                            elif ch3 == 'B':
                                if self.current_throttle - self.THROTTLE_STEP >= self.THROTTLE_MIN:
                                    self.current_throttle -= self.THROTTLE_STEP
                                    print "\nThrottle: %.1f%% (decreased)" % (self.current_throttle * 100)
                                else:
                                    print "\nMIN throttle! (%.1f%%)" % (self.THROTTLE_MIN * 100)

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
            self.send_direct_motors([0.0, 0.0, 0.0, 0.0])
            time.sleep(0.5)

            # Disarm
            print "Disarming..."
            self.disarm_motors()

            print "Motors stopped and disarmed"


def main():
    print "="*70
    print "HOVER STABILIZATION SYSTEM - PX4 OFFBOARD MODE"
    print "="*70
    print ""
    print "This script gives you direct motor control via PX4 OFFBOARD:"
    print "  - Reads IMU values (Roll, Pitch, Yaw)"
    print "  - Calibrates starting position as reference (0,0,0)"
    print "  - Calculates PID corrections based on tilt"
    print "  - Adjustable throttle with UP/DOWN arrows (starts at 25%%)"
    print "  - Sends attitude rate commands to PX4"
    print ""
    print "YOU are the flight controller!"
    print "PX4 follows your attitude rate commands."
    print ""
    print "NO special parameters needed for Intel Aero (2016 firmware)"
    print ""
    print "WARNING: Remove propellers for first test!"
    print ""

    raw_input("Press ENTER to start (Ctrl+C to cancel)...")
    print ""

    # Create stabilizer instance
    stabilizer = HoverStabilizerPX4()

    # Connect to flight controller
    stabilizer.connect()

    # Calibrate zero reference point
    stabilizer.calibrate_zero_reference()

    print "\nReady to start!"
    print ""
    raw_input("Press ENTER to begin stabilization...")

    # Run main control loop
    stabilizer.run()


if __name__ == "__main__":
    main()
