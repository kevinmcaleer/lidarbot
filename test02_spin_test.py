from machine import UART, Pin
import time
import struct

# Setup UART
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

PACKET_SIZE = 47
EXPECTED_ROTATION_TIME_MS = 100  # About 10Hz is normal

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

print("Starting LD06 Motor Spin Test...")
time.sleep(1)

# --- Capture Timestamps ---
timestamps = []

for _ in range(10):  # Capture 10 packets
    packet = read_packet()
    timestamp = struct.unpack('<H', packet[44:46])[0]
    timestamps.append(timestamp)
    print(f"Captured packet with timestamp {timestamp} ms")
    time.sleep(0.01)

# --- Analyze Timing ---
rotation_times = []
for i in range(1, len(timestamps)):
    diff = timestamps[i] - timestamps[i-1]
    if diff < 0:
        diff += 30000  # Handle wraparound at 30000 ms
    rotation_times.append(diff)

# --- Results ---
print("\n=== Spin Test Results ===")
for i, diff in enumerate(rotation_times):
    print(f"Time between packet {i} and {i+1}: {diff} ms")

avg_time = sum(rotation_times) / len(rotation_times)
print(f"\nAverage time between packets: {avg_time:.1f} ms")

if 70 <= avg_time <= 150:
    print("✅ Motor speed looks normal! (good spin)")
else:
    print("❌ Motor speed abnormal! (might be stuck or faulty)")
