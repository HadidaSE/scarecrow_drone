#!/usr/bin/env python2.7
"""
Simple barometer test - reads raw SCALED_PRESSURE messages
to see if the barometer hardware is working
"""

from dronekit import connect
import time

CONNECTION_STRING = '/dev/ttyS1'
BAUD_RATE = 1500000

print "=" * 50
print "Barometer Raw Test"
print "=" * 50
print "Connecting..."

vehicle = connect(CONNECTION_STRING, baud=BAUD_RATE, wait_ready=False)
print "Connected!"

# Store pressure readings
pressure_data = {'abs': None, 'diff': None, 'temp': None}
altitude_data = {'vfr': None, 'local': None, 'global': None, 'rangefinder': None}

def pressure_callback(vehicle, name, message):
    pressure_data['abs'] = message.press_abs  # hPa
    pressure_data['diff'] = message.press_diff  # hPa
    pressure_data['temp'] = message.temperature / 100.0  # cdegC to degC

def vfr_callback(vehicle, name, message):
    altitude_data['vfr'] = message.alt

def local_callback(vehicle, name, message):
    altitude_data['local'] = -message.z

def global_callback(vehicle, name, message):
    altitude_data['global'] = message.relative_alt / 1000.0  # mm to m

def rangefinder_callback(vehicle, name, message):
    altitude_data['rangefinder'] = message.distance

# Register listeners
vehicle.add_message_listener('SCALED_PRESSURE', pressure_callback)
vehicle.add_message_listener('SCALED_PRESSURE2', pressure_callback)
vehicle.add_message_listener('VFR_HUD', vfr_callback)
vehicle.add_message_listener('LOCAL_POSITION_NED', local_callback)
vehicle.add_message_listener('GLOBAL_POSITION_INT', global_callback)
vehicle.add_message_listener('RANGEFINDER', rangefinder_callback)

print "Waiting for data..."
time.sleep(3)

print ""
print "-" * 70
print "Time     | Pressure | Temp  | VFR Alt | Local Z | Global | Range"
print "-" * 70

try:
    initial_pressure = None
    while True:
        if pressure_data['abs'] is not None:
            if initial_pressure is None:
                initial_pressure = pressure_data['abs']

            # Calculate altitude change from pressure (rough estimate)
            # ~8.3m per hPa at sea level
            pressure_alt_change = (initial_pressure - pressure_data['abs']) * 8.3

            vfr = "N/A" if altitude_data['vfr'] is None else "%.1fm" % altitude_data['vfr']
            local = "N/A" if altitude_data['local'] is None else "%.2fm" % altitude_data['local']
            glob = "N/A" if altitude_data['global'] is None else "%.2fm" % altitude_data['global']
            rng = "N/A" if altitude_data['rangefinder'] is None else "%.2fm" % altitude_data['rangefinder']

            print "%s | %7.2f hPa (%+.2fm) | %.1fC | %7s | %7s | %6s | %s" % (
                time.strftime("%H:%M:%S"),
                pressure_data['abs'],
                pressure_alt_change,
                pressure_data['temp'],
                vfr,
                local,
                glob,
                rng
            )
        else:
            print "%s | Waiting for pressure data..." % time.strftime("%H:%M:%S")

        time.sleep(1)

except KeyboardInterrupt:
    print ""
    print "-" * 70
    print "Test stopped"

vehicle.close()
print "Done"
