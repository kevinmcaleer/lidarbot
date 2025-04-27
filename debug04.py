from machine import UART, Pin
import time
import struct

# --- Settings ---
NUM_PACKETS = 10  # Number of packets to capture
DISTANCE_MIN = 50    # mm
DISTANCE_MAX = 6000  # mm
CONFIDENCE_MIN = 10  # Minimum signal strength
PACKET_SIZE = 47

# --- UART Setup ---
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def read_byte():
    while not uart.any():
        time.sleep(0.001)
    return uart.read(1)

def read_packet():
    while True:
        if read_byte() == b'\x54':
            packet = b'\x54' + uart.read(46)
            if len(packet) == 47:
                return packet

# --- Start Test ---
print("Starting LD06 Sensor Health Test...")
time.sleep(1)

total_points = 0
good_points = 0
bad_points = 0

for packet_num in range(NUM_PACKETS):
    packet = read_packet()
    start_angle = struct.unpack('<H', packet[2:4])[0] / 100.0
    end_angle = struct.unpack('<H', packet[40:42])[0] / 100.0

    if end_angle < start_angle:
        angle_step = ((end_angle + 360) - start_angle) / 12
    else:
        angle_step = (end_angle - start_angle) / 12

    for i in range(0, 36, 3):
        distance = struct.unpack('<H', packet[4+i:6+i])[0]
        confidence = packet[6+i]

        total_points += 1

        if (DISTANCE_MIN <= distance <= DISTANCE_MAX) and (confidence >= CONFIDENCE_MIN):
            good_points += 1
        else:
            bad_points += 1

# --- Results ---
print("\n=== Sensor Test Results ===")
print(f"Total points measured : {total_points}")
print(f"Good points            : {good_points}")
print(f"Bad points             : {bad_points}")

good_percent = (good_points / total_points) * 100
print(f"\nSensor Health Score    : {good_percent:.1f}% good")

if good_percent > 90:
    print("✅ Sensor is healthy!")
elif good_percent > 70:
    print("⚠️ Sensor may be slightly dirty or disturbed.")
else:
    print("❌ Sensor might be dusty, misaligned, or damaged.")

print("===========================")
