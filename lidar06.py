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
        time.sleep(0.001)
    return uart.read(1)

def read_packet():
    # Wait for header
    while True:
        b = read_byte()
        if b == b'\x54':
            b2 = read_byte()
            if b2 == b'\x2c':
                # Packet starts
                packet = uart.read(45)  # Remaining 45 bytes
                return b'\x54\x2c' + packet


print("Streaming raw packets...")

count = 0

while count < 5:
    packet = read_packet()
    print(packet.hex())
    count += 1
