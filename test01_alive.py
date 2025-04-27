from machine import UART, Pin
import time

# Setup UART
uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def read_byte():
    while not uart.any():
        time.sleep(0.001)
    return uart.read(1)

print("Starting LD06 Alive Test...")
time.sleep(1)

found_headers = 0
total_bytes = 0
max_bytes = 500  # How many bytes to sample

while total_bytes < max_bytes:
    byte = read_byte()
    total_bytes += 1
    if byte == b'\x54':
        found_headers += 1
    if total_bytes % 50 == 0:
        print(f"Read {total_bytes} bytes... Found {found_headers} headers.")

# --- Results ---
print("\n=== Alive Test Results ===")
print(f"Total bytes read     : {total_bytes}")
print(f"Packets (0x54 headers) found : {found_headers}")

if found_headers > 5:
    print("✅ LIDAR seems alive and sending packets!")
else:
    print("❌ No or very few packets. LIDAR might be dead.")
