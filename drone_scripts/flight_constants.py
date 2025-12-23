#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Flight Constants - Calibrated PWM Values for Intel Aero RTF Drone
These values are calibrated for stable autonomous flight
"""

# ============================================================
# MOTOR PWM VALUES (Calibrated)
# ============================================================

# Hover - maintains stable altitude
HOVER_PWM = 1625

# Climb - ascends steadily
CLIMB_PWM = 1630

# Landing - controlled descent
LAND_PWM = 1510

# Neutral RC channels (roll, pitch, yaw centered)
NEUTRAL = 1500

# Minimum throttle (motors armed but minimal power)
THROTTLE_MIN = 1000

# Maximum throttle safety limit
THROTTLE_MAX = 2000


# ============================================================
# ALTITUDE CONTROL PARAMETERS
# ============================================================

# Default target altitude (meters above home)
DEFAULT_TARGET_ALTITUDE = 1.0

# Altitude tolerance (±meters) - within this range = hovering
ALTITUDE_TOLERANCE = 0.1

# Minimum altitude to consider "landed" (meters)
LANDING_ALTITUDE_THRESHOLD = 0.2


# ============================================================
# TIMING PARAMETERS
# ============================================================

# How often to sample altitude (seconds) - 50Hz
ALTITUDE_SAMPLE_RATE = 0.02

# How often to print status updates (seconds) - 5Hz
STATUS_UPDATE_RATE = 0.2

# How often to refresh RC override to prevent timeout (seconds)
RC_OVERRIDE_REFRESH_RATE = 0.1


# ============================================================
# CONNECTION PARAMETERS
# ============================================================

# Serial port for Intel Aero flight controller
SERIAL_PORT = '/dev/ttyS1'

# Baud rate for MAVLink connection
BAUD_RATE = 1500000

# Flight mode for autonomous control
FLIGHT_MODE = 'STABILIZED'
