from machine import UART, Pin, Timer
import time
import math

# UART setup
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))
nearest_target = ""

# --- CONFIGURATION CONSTANTS ---
DISTANCE_MIN = 10    # mm
DISTANCE_MAX = 6000  # mm (can be tuned)

CONFIDENCE_MIN = 5  # minimum confidence accepted (0-255)
CONFIDENCE_MAX = 255 # maximum confidence (optional, usually 255)

SCREEN_SIZE = 21
CENTER = SCREEN_SIZE // 2
MAX_RADIUS = CENTER - 2

def flush_uart(uart):
    print("Flushing UART...")
    time.sleep(0.5)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)
    time.sleep(0.5)

def read_byte():
    while not uart.any():
        time.sleep(0.0005)
    return uart.read(1)

def resync_to_header():
    while True:
        b1 = read_byte()
        if b1 == b'\x54':
            b2 = read_byte()
            if b2 == b'\x2c':
                return

def read_packet():
    resync_to_header()
    packet = uart.read(44)
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
        if not (DISTANCE_MIN <= distance <= DISTANCE_MAX):
            bad_points += 1
        if not (CONFIDENCE_MIN <= confidence <= CONFIDENCE_MAX):
            bad_points += 1
    return bad_points <= 6

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

    radar[CENTER][0] = 'W'  # West
    radar[CENTER][SCREEN_SIZE-1] = 'E'  # East
    radar[0][CENTER] = 'N'  # North
    radar[SCREEN_SIZE-1][CENTER] = 'S'  # South
    radar[CENTER][CENTER] = '+'


def plot_point(angle_deg, distance_mm):
    if not (50 < distance_mm < DISTANCE_THRESHOLD):
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
    global nearest_target
    print("\n" * 30)
    for row in radar:
        print(''.join(row))
    print()
    
    if nearest_target:
        angle, distance = nearest_target
        print(f"Nearest: {distance/10:.1f} cm at {angle:.1f}°")
    else:
        print("Nearest: None")


# --- Startup ---
flush_uart(uart)
clear_radar()

timer = Timer()
timer.init(period=200, mode=Timer.PERIODIC, callback=print_radar)  # Refresh 5 fps

print("Starting improved RADAR...")

bad_count = 0
last_angle = None

while True:
    packet = read_packet()
    start_angle, end_angle, points = parse_packet(packet)

    if not validate_packet(start_angle, end_angle, points):
        bad_count += 1
        continue

    bad_count = 0

    # Auto clear radar when a new sweep starts
    if last_angle is not None and start_angle < last_angle:
        clear_radar()

    last_angle = start_angle
    
    # After plotting points
    min_distance = DISTANCE_THRESHOLD
    min_angle = None

    for idx, (distance, confidence) in enumerate(points):
        if 50 < distance < min_distance:
            min_distance = distance
            min_angle = start_angle + angle_step * idx

    # Save the nearest target for display
    if min_angle is not None:
        nearest_target = (min_angle, min_distance)
    else:
        nearest_target = None


    # Plot points
    angle_step = (end_angle - start_angle) / max(len(points) - 1, 1)
    for idx, (distance, confidence) in enumerate(points):
        angle = start_angle + angle_step * idx
        plot_point(angle, distance)

    time.sleep(0.01)  # Breathing room
