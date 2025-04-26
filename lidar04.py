from machine import UART, Pin
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

# Radar screen setup
SCREEN_SIZE = 21
CENTER = SCREEN_SIZE // 2
MAX_RADIUS = CENTER - 2
DISTANCE_THRESHOLD = 1000  # mm

def create_radar():
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

# Main
radar = create_radar()

def read_byte():
    while not uart.any():
        time.sleep(0.001)
    return uart.read(1)

print("Waiting for packet...")

while True:
    byte = read_byte()

    if byte == b'\x54':
        second = read_byte()
        if second == b'\x2c':
            length_l = ord(read_byte())
            length_h = ord(read_byte())
            packet_len = (length_h << 8) | length_l

            start_angle_l = ord(read_byte())
            start_angle_h = ord(read_byte())
            end_angle_l = ord(read_byte())
            end_angle_h = ord(read_byte())
            timestamp_l = ord(read_byte())
            timestamp_h = ord(read_byte())

            start_angle = (start_angle_h << 8 | start_angle_l) / 100.0
            end_angle = (end_angle_h << 8 | end_angle_l) / 100.0

            points_expected = (packet_len - 5) // 3
            points_read = 0
            point_buffer = b''

            # Clean screen for next sweep
            radar = create_radar()

            # Read and plot points immediately
            while points_read < points_expected:
                point_buffer += read_byte()
                if len(point_buffer) >= 3:
                    # Inside while points_read < points_expected:
                    distance = point_buffer[0] | (point_buffer[1] << 8)
                    confidence = point_buffer[2]

                    # Add this line:
                    if confidence < 80:
                        point_buffer = b''
                        points_read += 1
                        continue  # Skip weak points

                    if points_expected > 1:
                        interp_angle = start_angle + (end_angle - start_angle) * (points_read / (points_expected - 1))
                    else:
                        interp_angle = start_angle

                    if interp_angle >= 360:
                        interp_angle -= 360

                    plot_point(radar, interp_angle, distance)

                    point_buffer = b''
                    points_read += 1


            # After finishing full sweep
            print_radar(radar)
            print("Waiting for next packet...")
