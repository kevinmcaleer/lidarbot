from machine import UART, Pin, Timer
import time
import math

# UART setup
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def flush_uart(uart):
    time.sleep(0.1)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)

flush_uart(uart)

# Radar setup
SCREEN_SIZE = 21
CENTER = SCREEN_SIZE // 2
MAX_RADIUS = CENTER - 2
DISTANCE_THRESHOLD = 1000  # mm (2 meters max range)
REFRESH = 250

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

    radar[CENTER][0] = '|'
    radar[CENTER][SCREEN_SIZE-1] = '|'
    radar[0][CENTER] = '-'
    radar[SCREEN_SIZE-1][CENTER] = '-'
    radar[CENTER][CENTER] = '+'

def plot_point(angle_deg, distance_mm):
    if not (10 < distance_mm < DISTANCE_THRESHOLD):
        return

    radius = int((distance_mm / DISTANCE_THRESHOLD) * MAX_RADIUS)
    if radius > MAX_RADIUS:
        radius = MAX_RADIUS

    angle_rad = math.radians(angle_deg)
    x = int(CENTER + radius * math.cos(angle_rad))
    y = int(CENTER - radius * math.sin(angle_rad))

    if 0 <= x < SCREEN_SIZE and 0 <= y < SCREEN_SIZE:
        radar[y][x] = '•'

def print_radar(timer=None):
    print("\033[2J\033[H", end='')  # Clear screen
    for row in radar:
        print(''.join(row))
    print()
    clear_radar()

def read_byte():
    while not uart.any():
        time.sleep(0.001)
    return uart.read(1)

def read_packet():
    # Wait for header
    while True:
        b = read_byte()
        if b == b'\x54':
            b2 = read_byte()
            if b2 == b'\x2c':
                packet = uart.read(45)
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

# Setup radar
clear_radar()

# Start radar refresh timer
timer = Timer()
timer.init(period=REFRESH, mode=Timer.PERIODIC, callback=print_radar)

print("Streaming radar points...")

# State
current_angle = 0.0  # Rolling angle

while True:
    packet = read_packet()
    start_angle, end_angle, points = parse_packet(packet)

    for idx, (distance, confidence) in enumerate(points):
        if confidence > 10:
            # Interpolate angle across points
            if end_angle >= start_angle:
                angle_range = end_angle - start_angle
            else:
                angle_range = (end_angle + 360) - start_angle

            interp_angle = (start_angle + (idx / (len(points)-1)) * angle_range) % 360

            plot_point(interp_angle, distance)
