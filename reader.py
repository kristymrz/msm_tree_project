import serial
import time
import pygame
import os
import random

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
pygame.mixer.set_num_channels(16)

# Default audio files per pin
default_audio_files = {
    2: "01-BDE_Monster_01.wav",
    15: "01-E_Monster_01.wav",
    13: "01-BE_Monster_01.wav",
    12: "01-BD_Monster_01.wav",   # GPIO12 reserved for mode switch
    32: "01-BD_Monster_01.wav",
    33: "01-G_Monster_01.wav",
    27: "01-Z01_Monster_01.wav",
}

# ---- Gather all audio files in /audio ----
all_audio_files = [f for f in os.listdir("audio") if f.endswith(".wav")]

# Map pin to currently assigned sound
assigned_audio_files = default_audio_files.copy()
assigned_sounds = {}
for pin, fname in assigned_audio_files.items():
    path = os.path.join("audio", fname)
    if not os.path.exists(path):
        print(f"Audio file missing: {path}")
        exit(1)
    assigned_sounds[pin] = pygame.mixer.Sound(path)

# ---- Touch state tracking ----
touch_states = {pin: False for pin in assigned_audio_files.keys()}
touch_start_time = {pin: 0 for pin in assigned_audio_files.keys()}
last_tap_time = {pin: 0 for pin in assigned_audio_files.keys()}

# ---- Mode tracking ----
mode = 1  # 1 = hold-to-play, 2 = click-to-toggle
click_toggle_states = {pin: False for pin in assigned_audio_files.keys()}  # for Mode 2

# ---- Timing constants ----
DOUBLE_TAP_MAX_INTERVAL = 0.5   # max seconds between taps to count as double tap
DOUBLE_TAP_MIN_INTERVAL = 0.02  # lowered for very quick double taps
TAP_MAX_DURATION = 0.25         # max duration of touch to count as tap for normal pins
TAP_MAX_DURATION_MODE_BTN = 0.5 # max duration to count as tap for GPIO12
TAP_MIN_DURATION = 0.02         # ignore accidental micro-taps

MODE_SWITCH_PIN = 12  # GPIO12 reserved for mode switching

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
            continue

        current_time = time.time()

        if state == 1 and not touch_states.get(pin, False):
            # Touch started
            touch_states[pin] = True
            touch_start_time[pin] = current_time

            # Mode 2 click behavior: toggle audio
            if mode == 2 and pin != MODE_SWITCH_PIN:
                if click_toggle_states[pin]:
                    assigned_sounds[pin].stop()
                    click_toggle_states[pin] = False
                    print(f"Pin {pin} clicked — stopped audio: {assigned_audio_files[pin]}")
                else:
                    assigned_sounds[pin].play(-1)
                    click_toggle_states[pin] = True
                    print(f"Pin {pin} clicked — started audio: {assigned_audio_files[pin]}")

            # Mode 1 hold behavior: play while holding
            elif mode == 1 and pin != MODE_SWITCH_PIN:
                assigned_sounds[pin].play(-1)
                print(f"Pin {pin} pressed — playing assigned audio: {assigned_audio_files[pin]}")

        elif state == 0 and touch_states.get(pin, False):
            # Touch released
            touch_states[pin] = False
            touch_duration = current_time - touch_start_time[pin]

            # ---- GPIO12: mode switcher ----
            if pin == MODE_SWITCH_PIN and TAP_MIN_DURATION < touch_duration <= TAP_MAX_DURATION_MODE_BTN:
                # Stop all audio immediately
                for s in assigned_sounds.values():
                    s.stop()
                click_toggle_states = {p: False for p in click_toggle_states}  # reset toggles

                # Toggle mode
                mode = 2 if mode == 1 else 1
                print(f"Mode switched! Current mode: {mode}")

            # ---- Double tap reassignment (for normal pins only) ----
            elif pin != MODE_SWITCH_PIN and touch_duration <= TAP_MAX_DURATION:
                interval_since_last_tap = current_time - last_tap_time[pin]
                if DOUBLE_TAP_MIN_INTERVAL < interval_since_last_tap <= DOUBLE_TAP_MAX_INTERVAL:
                    # Stop old sound first to prevent overlap
                    assigned_sounds[pin].stop()
                    click_toggle_states[pin] = False  # reset toggle state for Mode 2

                    # Reassign random audio
                    available_files = [f for f in all_audio_files if f != assigned_audio_files[pin]]
                    if available_files:
                        new_file = random.choice(available_files)
                        assigned_audio_files[pin] = new_file
                        assigned_sounds[pin] = pygame.mixer.Sound(os.path.join("audio", new_file))
                        print(f"Pin {pin} double tapped — reassigned audio: {new_file}")
                last_tap_time[pin] = current_time

            # ---- Stop audio for Mode 1 on release (normal pins) ----
            if mode == 1 and pin != MODE_SWITCH_PIN:
                assigned_sounds[pin].stop()
                print(f"Pin {pin} released — stopped audio: {assigned_audio_files[pin]}")

    time.sleep(0.01)