from machine import UART, Pin
import time

# --- Configuration ---
DISTANCE_MIN = 50
DISTANCE_MAX = 6000
CONFIDENCE_MIN = 10
PACKET_SIZE = 47

# --- Setup UART ---
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def flush_uart(uart):
    print("Flushing UART...")
    time.sleep(0.5)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)
    time.sleep(0.5)

flush_uart(uart)

def read_byte():
    while not uart.any():
        time.sleep(0.001)
    return uart.read(1)

def read_packet():
    # Sync to header
    while True:
        byte = read_byte()
        if byte == b'\x54':
            packet = byte + uart.read(PACKET_SIZE - 1)
            if len(packet) == PACKET_SIZE:
                return packet

def validate_packet(packet):
    ver_len = packet[1]
    speed = packet[2] | (packet[3] << 8)
    start_angle = (packet[4] | (packet[5] << 8)) / 100.0

    points = []
    for i in range(12):
        offset = 6 + i * 3
        dist = packet[offset] | (packet[offset + 1] << 8)
        conf = packet[offset + 2]
        points.append((dist, conf))

    end_angle = (packet[42] | (packet[43] << 8)) / 100.0
    timestamp = packet[44] | (packet[45] << 8)
    crc = packet[46]

    print("-" * 40)
    print(f"Packet:")
    print(f" Start Angle : {start_angle:.2f}°")
    print(f" End Angle   : {end_angle:.2f}°")
    print(f" Speed       : {speed} deg/sec")
    print(f" Timestamp   : {timestamp} ms")
    print(f" CRC8        : {crc}")
    print(f" Points:")

    for idx, (distance, confidence) in enumerate(points):
        validity = "✅ OK"
        if not (DISTANCE_MIN <= distance <= DISTANCE_MAX):
            validity = "❌ BAD DIST"
        if confidence < CONFIDENCE_MIN:
            validity = "❌ BAD CONF"

        print(f"  Point {idx+1:2}: Distance = {distance:5} mm | Confidence = {confidence:3} --> {validity}")

print("Starting LD06 validation...")

# --- Main Loop ---
while True:
    packet = read_packet()
    validate_packet(packet)
