from machine import UART, Pin
import time

# UART setup
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def flush_uart(uart):
    time.sleep(0.1)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)

flush_uart(uart)

def read_byte():
    while not uart.any():
        time.sleep(0.0005)
    return uart.read(1)

def resync_to_header():
    """Keep reading until we see 0x54 0x2C."""
    while True:
        b1 = read_byte()
        if b1 == b'\x54':
            b2 = read_byte()
            if b2 == b'\x2c':
                return

def read_packet():
    resync_to_header()  # Always start clean
    packet = uart.read(44)  # 44 bytes after header
    return b'\x54\x2c' + packet

def parse_packet(packet):
    start_angle = (packet[4] | (packet[5] << 8)) / 100
    end_angle = (packet[6] | (packet[7] << 8)) / 100

    points = []
    for i in range(12):
        offset = 8 + i * 3
        distance = packet[offset] | (packet[offset + 1] << 8)
        confidence = packet[offset + 2]
        points.append((distance, confidence))

    return start_angle, end_angle, points

def validate_packet(start_angle, end_angle, points):
    bad_points = 0
    for distance, confidence in points:
        if not (50 <= distance <= 6000):
            bad_points += 1
        if not (10 <= confidence <= 255):
            bad_points += 1

    if bad_points > 6:
        return False  # Too many bad points
    return True

print("Starting LD06 validation...")

bad_count = 0

while True:
    packet = read_packet()
    start_angle, end_angle, points = parse_packet(packet)

    if not validate_packet(start_angle, end_angle, points):
        bad_count += 1
        if bad_count % 10 == 0:
            print("...still syncing...")
        continue

    print("\n✅ Valid packet:")
    print(f" Start Angle: {start_angle:.2f}°")
    print(f" End Angle  : {end_angle:.2f}°")
    print(" Points:")
    for idx, (distance, confidence) in enumerate(points):
        print(f"  Point {idx+1:2d}: Distance = {distance:5d} mm | Confidence = {confidence:3d}")

    bad_count = 0  # Reset after first good packet
    time.sleep(0.1)
