from machine import UART, Pin
import time
import math

# Setup UART
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def flush_uart(uart):
    print('initialising')
    time.sleep(0.1)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)
    print('done.')

flush_uart(uart)

# Read full packet
def read_packet():
    buffer = b''
    while True:
        if uart.any():
            byte = uart.read(1)
            if not byte:
                continue
            buffer += byte

            if len(buffer) >= 2 and buffer[-2:] == b'\xaa\x55':
                while uart.any() < 2:
                    time.sleep(0.001)
                length_bytes = uart.read(2)
                packet_len = length_bytes[0] | (length_bytes[1] << 8)

                while uart.any() < packet_len:
                    time.sleep(0.001)
                packet = uart.read(packet_len)

                return b'\xaa\x55' + length_bytes + packet

# Parse packet
def parse_packet(packet):
    if packet[0] != 0xAA or packet[1] != 0x55:
        return []

    packet_len = packet[2] | (packet[3] << 8)
    start_angle = (packet[4] | (packet[5] << 8)) / 100
    end_angle = (packet[6] | (packet[7] << 8)) / 100

    points = []
    num_points = (packet_len - 5) // 3

    for i in range(num_points):
        offset = 8 + i * 3
        distance = packet[offset] | (packet[offset + 1] << 8)
        confidence = packet[offset + 2]

        if end_angle >= start_angle:
            angle = start_angle + (end_angle - start_angle) * (i / (num_points - 1))
        else:
            angle = start_angle + (end_angle + 360 - start_angle) * (i / (num_points - 1))
            if angle >= 360:
                angle -= 360

        points.append((angle, distance, confidence))

    return points

# Radar screen setup
SCREEN_SIZE = 21
CENTER = SCREEN_SIZE // 2
MAX_RADIUS = CENTER - 2  # Leave room for border
DISTANCE_THRESHOLD = 1000  # mm

def create_radar():
    radar = [[' ' for _ in range(SCREEN_SIZE)] for _ in range(SCREEN_SIZE)]

    # Draw outer circle
    for y in range(SCREEN_SIZE):
        for x in range(SCREEN_SIZE):
            dx = x - CENTER
            dy = y - CENTER
            dist = math.sqrt(dx*dx + dy*dy)
            if MAX_RADIUS - 0.5 < dist < MAX_RADIUS + 0.5:
                radar[y][x] = 'o'  # Circle edge

    # Draw cross markers
    radar[CENTER][0] = '|'
    radar[CENTER][SCREEN_SIZE-1] = '|'
    radar[0][CENTER] = '-'
    radar[SCREEN_SIZE-1][CENTER] = '-'
    radar[CENTER][CENTER] = '+'

    return radar

def plot_point(radar, angle_deg, distance_mm):
    if distance_mm > DISTANCE_THRESHOLD:
        return

    radius = int((distance_mm / DISTANCE_THRESHOLD) * MAX_RADIUS)
    if radius > MAX_RADIUS:
        radius = MAX_RADIUS

    angle_rad = math.radians(angle_deg)
    x = int(CENTER + radius * math.cos(angle_rad))
    y = int(CENTER - radius * math.sin(angle_rad))

    if 0 <= x < SCREEN_SIZE and 0 <= y < SCREEN_SIZE:
        radar[y][x] = '•'

def print_radar(radar):
    print("\033[2J\033[H", end='')  # Clear screen
    for row in radar:
        print(''.join(row))
    print()

# Main loop
while True:
    packet = read_packet()
    if packet:
        points = parse_packet(packet)
        radar = create_radar()
        for angle, distance, confidence in points:
            plot_point(radar, angle, distance)
        print_radar(radar)
    time.sleep(0.05)
