from machine import UART, Pin
import time

uart = UART(0, baudrate=230400, tx=Pin(0), rx=Pin(1))

def flush_uart(uart):
    print("Flushing UART...")
    time.sleep(0.5)
    while uart.any():
        uart.read(32)
        time.sleep(0.001)
    time.sleep(0.5)

flush_uart(uart)

print("Dumping 200 bytes of raw UART data...")

byte_count = 0
max_bytes = 200  # or 300 if you want

while byte_count < max_bytes:
    if uart.any():
        byte = uart.read(1)
        if byte:
            print(byte.hex(), end=' ')
            byte_count += 1

print("\nDone reading raw bytes.")
