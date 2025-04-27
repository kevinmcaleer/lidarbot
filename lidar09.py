from machine import UART, Pin
import time
import struct

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

def detect_object(packet):
    start_angle = struct.unpack('<H', packet[2:4])[0] / 100.0
    end_angle = struct.unpack('<H', packet[40:42])[0] / 100.0

    if end_angle < start_angle:
        angle_step = ((end_angle + 360) - start_angle) / 12
    else:
        angle_step = (end_angle - start_angle) / 12

    for i in range(0, 36, 3):
        dist = struct.unpack('<H', packet[4+i:6+i])[0]
        angle = (start_angle + (i//3) * angle_step) % 360
        if angle > 180:
            angle -= 360  # Normalize to [-180, 180]

        if -45 <= angle <= 45:
            if 50 < dist < 3000:  # only distances between 5cm and 300cm
                print(f"🚗 Object detected at {dist/10:.1f} cm, angle {angle:.1f}°")
                return
    print("✅ No object ahead.")

# --- Main Loop ---
print("Starting simple object detection...")

while True:
    packet = read_packet()
    detect_object(packet)
    time.sleep(0.1)
