#!/usr/bin/env python2.7
"""
Raw MAVLink message dump - see what messages the FC is actually sending
"""

from pymavlink import mavutil
import time

print "=" * 50
print "Raw MAVLink Message Dump"
print "=" * 50
print "Connecting..."

master = mavutil.mavlink_connection('/dev/ttyS1', baud=1500000)
master.wait_heartbeat()
print "Connected! System %u Component %u" % (master.target_system, master.target_component)

# Track what messages we receive
message_counts = {}

print ""
print "Monitoring messages for 10 seconds..."
print ""

start_time = time.time()
while (time.time() - start_time) < 10:
    msg = master.recv_match(blocking=False)
    if msg:
        msg_type = msg.get_type()
        if msg_type not in message_counts:
            message_counts[msg_type] = 0
            # Print first occurrence of each message type
            print "NEW: %s" % msg_type
            if hasattr(msg, 'to_dict'):
                d = msg.to_dict()
                # Print interesting fields
                for key in ['alt', 'relative_alt', 'z', 'press_abs', 'xacc', 'yacc', 'zacc']:
                    if key in d:
                        print "  %s = %s" % (key, d[key])
        message_counts[msg_type] += 1
    time.sleep(0.001)

print ""
print "=" * 50
print "Message Summary (counts):"
print "=" * 50
for msg_type in sorted(message_counts.keys()):
    print "  %s: %d" % (msg_type, message_counts[msg_type])

master.close()
print ""
print "Done"
