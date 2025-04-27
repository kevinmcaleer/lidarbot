from machine import UART, Pin
import time
import math

# --- CONFIGURATION CONSTANTS ---
DISTANCE_MIN = 50     # Minimum distance in mm
DISTANCE_MAX = 6000   # Maximum distance in mm
CONFIDENCE_MIN = 100   # Minimum confidence to accept point

SCREEN_SIZE = 21
CENTER = SCREEN_SIZE // 2
MAX_RADIUS = CENTER - 2

PACKET_SIZE = 47  # Fixed LD06 packet size

uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def flush_uart(uart):
    print("Flushing UART...")
    time.sleep(0.5)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)
    time.sleep(0.5)

flush_uart(uart)

# --- Radar display setup ---
radar = [[' ' for _ in range(SCREEN_SIZE)] for _ in range(SCREEN_SIZE)]

def clear_radar():
    global radar
    radar = [[' ' for _ in range(SCREEN_SIZE)] for _ in range(SCREEN_SIZE)]
    for y in range(SCREEN_SIZE):
        for x in range(SCREEN_SIZE):
            dx = x - CENTER
            dy = y - CENTER
            dist = math.sqrt(dx*dx + dy*dy)
            if MAX_RADIUS - 0.5 < dist < MAX_RADIUS + 0.5:
                radar[y][x] = 'o'
    radar[CENTER][0] = 'W'
    radar[CENTER][SCREEN_SIZE-1] = 'E'
    radar[0][CENTER] = 'N'
    radar[SCREEN_SIZE-1][CENTER] = 'S'
    radar[CENTER][CENTER] = '+'

def plot_point(angle_deg, distance_mm):
    if not (DISTANCE_MIN <= distance_mm <= DISTANCE_MAX):
        return

    radius = int((distance_mm / DISTANCE_MAX) * MAX_RADIUS)
    if radius > MAX_RADIUS:
        radius = MAX_RADIUS

    angle_rad = math.radians(angle_deg)
    x = int(CENTER + radius * math.cos(angle_rad))
    y = int(CENTER - radius * math.sin(angle_rad))

    if 0 <= x < SCREEN_SIZE and 0 <= y < SCREEN_SIZE:
        radar[y][x] = '•'

def print_radar():
    print("\n" * 5)
    for row in radar:
        print(''.join(row))
    print()

def read_byte():
    while not uart.any():
        time.sleep(0.001)
    return uart.read(1)

def read_packet():
    # Sync to header
    while True:
        byte = read_byte()
        if byte == b'\x54':
            # Read rest of packet
            packet = byte + uart.read(PACKET_SIZE - 1)
            if len(packet) == PACKET_SIZE:
                return packet

def parse_packet(packet):
    # Packet fields according to spec
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

    return start_angle, end_angle, points

# --- Main loop ---
clear_radar()

print("Starting LD06 radar parsing...")

while True:
    packet = read_packet()
    start_angle, end_angle, points = parse_packet(packet)

    # Calculate step per point
    angle_diff = end_angle - start_angle
    if angle_diff < 0:
        angle_diff += 360.0
    angle_step = angle_diff / (len(points) - 1)

    # Plot valid points
    for idx, (distance, confidence) in enumerate(points):
        if confidence >= CONFIDENCE_MIN:
            angle = start_angle + angle_step * idx
            plot_point(angle, distance)

    print_radar()
    clear_radar()
