from machine import UART, Pin
import time
import struct

# --- UART Setup ---
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

PACKET_SIZE = 47
FULL_ROTATION_DEGREES = 360
MEASURED_DEGREES_PER_PACKET = 30  # Rough estimate for LD06

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

print("Starting LD06 Pro-Level RPM Test...")
time.sleep(1)

# --- Collect Data ---
timestamps = []
angles = []

for _ in range(12):  # Capture 12 packets
    packet = read_packet()
    start_angle = struct.unpack('<H', packet[2:4])[0] / 100.0
    timestamp = struct.unpack('<H', packet[44:46])[0]
    timestamps.append(timestamp)
    angles.append(start_angle)
    print(f"Captured packet: Start Angle {start_angle:.2f}°, Timestamp {timestamp} ms")
    time.sleep(0.01)

# --- Calculate Rotation Speed ---
total_angle = 0
total_time_ms = 0

for i in range(1, len(angles)):
    angle_diff = angles[i] - angles[i-1]
    if angle_diff < 0:
        angle_diff += 360
    total_angle += angle_diff

    time_diff = timestamps[i] - timestamps[i-1]
    if time_diff < 0:
        time_diff += 30000  # Handle wraparound
    total_time_ms += time_diff

print("\n=== Pro-Level RPM Test Results ===")
print(f"Total angle covered: {total_angle:.1f}°")
print(f"Total time: {total_time_ms} ms")

if total_angle == 0:
    print("❌ No angle movement detected. Sensor might be stuck.")
else:
    rotations = total_angle / 360.0
    time_minutes = total_time_ms / 60000.0
    rpm = rotations / time_minutes
    print(f"\nEstimated RPM: {rpm:.1f} RPM")

    if 300 <= rpm <= 600:
        print("✅ Motor RPM is within normal range!")
    else:
        print("❌ Motor RPM abnormal! Might be too slow or too fast.")


print("===============================")
