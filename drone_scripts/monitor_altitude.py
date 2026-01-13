#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Altitude Monitor - Fixed version that actually works
Reads ALL messages from buffer, extracts latest of each type
"""

from dronekit import connect
import time

def monitor_altitude():
    print "="*60
    print "ALTITUDE MONITOR - ALL SENSORS"
    print "="*60
    print ""

    vehicle = None

    try:
        # Connect
        print "Connecting to /dev/ttyS1..."
        vehicle = connect('/dev/ttyS1',
                         wait_ready=False,
                         baud=1500000,
                         heartbeat_timeout=30,
                         source_system=255)

        print "Connected!"
        time.sleep(1)

        # Flush buffer
        print "Flushing buffer..."
        for _ in range(100):
            try:
                vehicle._master.recv_msg()
            except:
                pass

        time.sleep(0.5)

        # Initial values
        home_baro = None
        home_gps = None
        home_z = None

        # Latest readings
        last_baro = None
        last_gps = None
        last_z = None

        # GPS stabilization - average first 10 readings
        gps_samples = []
        GPS_SAMPLES_NEEDED = 10

        print ""
        print "Waiting for GPS to stabilize (averaging first %d readings)..." % GPS_SAMPLES_NEEDED
        print ""

        # Collect GPS samples for home position
        while len(gps_samples) < GPS_SAMPLES_NEEDED:
            # Read ALL messages to keep connection alive
            for _ in range(50):
                try:
                    msg = vehicle._master.recv_msg()
                    if msg is None:
                        break

                    if msg.get_type() == 'GPS_RAW_INT':
                        gps_alt = msg.alt / 1000.0
                        gps_samples.append(gps_alt)
                        print "GPS sample %d/%d: %.2f m" % (len(gps_samples), GPS_SAMPLES_NEEDED, gps_alt)
                        if len(gps_samples) >= GPS_SAMPLES_NEEDED:
                            break
                except:
                    pass
            time.sleep(0.1)

        # Calculate average GPS home position
        home_gps = sum(gps_samples) / len(gps_samples)
        print ""
        print "GPS home position set to: %.2f m (average of %d samples)" % (home_gps, len(gps_samples))
        print "GPS altitude variation: %.2f m" % (max(gps_samples) - min(gps_samples))
        print ""

        print "Monitoring altitude (10 Hz updates)..."
        print "ALL VALUES = HEIGHT ABOVE GROUND"
        print ""
        print "%-8s | %-12s | %-12s | %-12s" % (
            "Time", "Barometer", "GPS", "IMU Z"
        )
        print "-"*60

        start_time = time.time()

        while True:
            current_time = time.time() - start_time

            # Read ALL available messages from buffer
            for _ in range(50):  # Read up to 50 messages per cycle
                try:
                    msg = vehicle._master.recv_msg()
                    if msg is None:
                        break

                    msg_type = msg.get_type()

                    # Extract altitude from ALTITUDE message
                    if msg_type == 'ALTITUDE':
                        baro_alt = msg.altitude_local
                        if home_baro is None:
                            home_baro = baro_alt
                        last_baro = baro_alt - home_baro

                    # Extract GPS altitude
                    elif msg_type == 'GPS_RAW_INT':
                        gps_alt = msg.alt / 1000.0
                        last_gps = gps_alt - home_gps

                    # Extract IMU Z
                    elif msg_type == 'LOCAL_POSITION_NED':
                        z_alt = -msg.z
                        if home_z is None:
                            home_z = z_alt
                        last_z = z_alt - home_z

                except:
                    pass

            # Format output
            baro_str = "%.2f m" % last_baro if last_baro is not None else "N/A"
            gps_str = "%.2f m" % last_gps if last_gps is not None else "N/A"
            z_str = "%.2f m" % last_z if last_z is not None else "N/A"

            print "%-8.1fs | %-12s | %-12s | %-12s" % (
                current_time, baro_str, gps_str, z_str
            )

            time.sleep(0.1)  # 10 Hz

    except KeyboardInterrupt:
        print ""
        print "\n" + "="*60
        print "STOPPED"
        print "="*60

    except Exception as e:
        print "\nERROR: %s" % str(e)
        import traceback
        traceback.print_exc()

    finally:
        if vehicle:
            vehicle.close()

if __name__ == "__main__":
    monitor_altitude()
