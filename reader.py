import serial
import time
import pygame
import os

# ---- Serial setup ----
PORT = "/dev/cu.usbserial-59270097101"  # replace with your ESP32 port
BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
except serial.SerialException:
    print(f"Cannot open serial port {PORT}.")
    exit(1)

# ---- Audio setup ----
pygame.mixer.init()
pygame.mixer.set_num_channels(16)  # enough channels for 7 sounds

# Map TTGO GPIOs to audio files
audio_files = {
    2: "01-BDE_Monster_01.wav",   # TOUCH2
    15: "01-E_Monster_01.wav",    # TOUCH3
    13: "01-BE_Monster_01.wav",   # TOUCH4
    12: "01-BD_Monster_01.wav",   # TOUCH5
    32: "01-BD_Monster_01.wav",   # TOUCH9
    33: "01-G_Monster_01.wav",    # TOUCH8
    27: "01-Z01_Monster_01.wav",  # TOUCH7
}

# Load sound objects and track states
sounds = {}
touch_states = {}
for pin, filename in audio_files.items():
    path = os.path.join(os.path.dirname(__file__), "audio", filename)
    if not os.path.exists(path):
        print(f"Audio file missing: {path}")
        exit(1)
    sounds[pin] = pygame.mixer.Sound(path)
    touch_states[pin] = False  # initially not touched

print("Listening for ESP32 touch data...")

while True:
    if ser.in_waiting:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue

        try:
            pin_str, state_str = line.split(",")
            pin = int(pin_str)
            state = int(state_str)
        except ValueError:
            continue  # ignore malformed lines

        # Only act if state has changed
        if state == 1 and not touch_states.get(pin, False):
            touch_states[pin] = True
            sounds[pin].play(-1)  # loop while pressed
            print(f"Pin {pin} pressed — audio started")

        elif state == 0 and touch_states.get(pin, False):
            touch_states[pin] = False
            sounds[pin].stop()
            print(f"Pin {pin} released — audio stopped")

    time.sleep(0.01)