"""
DrillSense — Live Data Logger & Visualization System

This script performs real-time:
- Serial data acquisition from Arduino
- CSV logging during controlled trials
- Live 4-panel sensor visualization

Features:
- Trial-based recording (ENTER to start)
- Emergency stop (ESC)
- Live plotting using Matplotlib
"""

import serial
import csv
import os
import time
import threading
import keyboard
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
PORT       = "COM9"
BAUD       = 115200
SAVE_DIR = r"C:\Users\YourName\Desktop\DrillSense\data\raw" # Update this directory path
MAX_POINTS = 200   # Buffer size for live plots

# ─────────────────────────────────────────────
# System State Variables
# ─────────────────────────────────────────────
trial_no  = 0      # Current experiment trial number
recording = False  # Data logging flag
exit_flag = False  # Program exit flag

# ─────────────────────────────────────────────
# File Handling (Auto-increment file naming)
# ─────────────────────────────────────────────
def get_next_filename(folder):
    """Create a new CSV file without overwriting existing logs."""
    i = 1
    while os.path.exists(os.path.join(folder, f"data_log_{i}.csv")):
        i += 1
    return os.path.join(folder, f"data_log_{i}.csv")

os.makedirs(SAVE_DIR, exist_ok=True)
filepath = get_next_filename(SAVE_DIR)

print(f"Saving to: {filepath}")
print("Press ENTER to start Trial 1...")

# ─────────────────────────────────────────────
# Data Buffers (for live plotting)
# ─────────────────────────────────────────────
timestamps   = deque(maxlen=MAX_POINTS)
current_buf  = deque(maxlen=MAX_POINTS)
power_buf    = deque(maxlen=MAX_POINTS)
lm35_buf     = deque(maxlen=MAX_POINTS)
dht_temp_buf = deque(maxlen=MAX_POINTS)
humidity_buf = deque(maxlen=MAX_POINTS)
vib_buf      = deque(maxlen=MAX_POINTS)

# ─────────────────────────────────────────────
# Serial + CSV Initialization
# ─────────────────────────────────────────────
ser = serial.Serial(PORT, BAUD, timeout=2)

csvfile = open(filepath, "w", newline="")
writer  = csv.writer(csvfile)

time.sleep(2)        # Allow Arduino reset
ser.flushInput()

# CSV Header (must match Arduino output format)
writer.writerow([
    "Timestamp", "Trial_No", "Current_A", "Power_VA",
    "LM35_Temp_C", "DHT_Temp_C", "Humidity_%",
    "Vibration", "Vib_Strength"
])

csvfile.flush()

# ─────────────────────────────────────────────
# Keyboard Listener Thread (Trial Control)
# ─────────────────────────────────────────────
def keyboard_listener():
    """Handles ENTER (start trial) and ESC (exit program)."""
    global trial_no, recording, exit_flag

    while not exit_flag:

        # Start new trial
        if keyboard.is_pressed("enter"):
            trial_no += 1
            recording = True
            print(f"\nTrial {trial_no} started")
            time.sleep(0.4)  # debounce

        # Stop program
        if keyboard.is_pressed("esc"):
            print("\nStopping program...")
            exit_flag = True
            break

        time.sleep(0.05)

# Start background thread
threading.Thread(target=keyboard_listener, daemon=True).start()

# ─────────────────────────────────────────────
# Matplotlib Setup (Live Dashboard)
# ─────────────────────────────────────────────
fig, axes = plt.subplots(4, 1, figsize=(12, 10))
fig.suptitle("Live Sensor Dashboard", fontsize=14)
plt.tight_layout(pad=3.0)

ax_current  = axes[0]
ax_temp     = axes[1]
ax_humidity = axes[2]
ax_vib      = axes[3]

# ─────────────────────────────────────────────
# Serial Parsing Function
# ─────────────────────────────────────────────
def parse_line(line):
    """Convert Arduino CSV string into Python dictionary."""
    parts = line.split(",")

    if len(parts) != 8:
        return None

    try:
        return {
            "timestamp": parts[0].strip(),
            "current"  : float(parts[1]),
            "power"    : float(parts[2]),
            "lm35"     : float(parts[3]),
            "dht_temp" : None if parts[4].strip() == "NA" else float(parts[4]),
            "humidity" : None if parts[5].strip() == "NA" else float(parts[5]),
            "vib"      : 1 if parts[6].strip() == "YES" else 0,
            "vib_str"  : int(parts[7])
        }

    except:
        return None

# ─────────────────────────────────────────────
# Main Animation Loop (Runs every 50ms)
# ─────────────────────────────────────────────
def animate(frame):
    global exit_flag

    # Exit handling
    if exit_flag:
        csvfile.close()
        ser.close()
        plt.close("all")
        print(f"File saved: {filepath}")
        return

    # Read serial buffer
    while ser.in_waiting:
        try:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue

            data = parse_line(line)
            if data is None:
                continue

            # Save only during active trial
            if recording:
                writer.writerow([
                    data["timestamp"], trial_no,
                    data["current"], data["power"],
                    data["lm35"],
                    data["dht_temp"] if data["dht_temp"] is not None else "NA",
                    data["humidity"] if data["humidity"] is not None else "NA",
                    "YES" if data["vib"] else "NO",
                    data["vib_str"]
                ])
                csvfile.flush()

            # Update live buffers
            timestamps.append(data["timestamp"])
            current_buf.append(data["current"])
            power_buf.append(data["power"])
            lm35_buf.append(data["lm35"])
            dht_temp_buf.append(data["dht_temp"] if data["dht_temp"] else 0)
            humidity_buf.append(data["humidity"] if data["humidity"] else 0)
            vib_buf.append(data["vib_str"])

        except:
            continue

    x = range(len(timestamps))

    # ── Current Plot ─────────────────────────
    ax_current.cla()
    ax_current.plot(x, current_buf, label="Current (A)")
    ax_current.plot(x, [p/220 for p in power_buf], linestyle="--", label="Power/220")
    ax_current.set_title("Current & Power")
    ax_current.legend()
    ax_current.grid(True)

    # ── Temperature Plot ─────────────────────
    ax_temp.cla()
    ax_temp.plot(x, lm35_buf, label="LM35")
    ax_temp.plot(x, dht_temp_buf, label="DHT11")
    ax_temp.set_title("Temperature")
    ax_temp.legend()
    ax_temp.grid(True)

    # ── Humidity Plot ────────────────────────
    ax_humidity.cla()
    ax_humidity.plot(x, humidity_buf, label="Humidity")
    ax_humidity.set_title("Humidity")
    ax_humidity.legend()
    ax_humidity.grid(True)

    # ── Vibration Plot ───────────────────────
    ax_vib.cla()
    ax_vib.plot(x, vib_buf, label="Vibration Strength")
    ax_vib.axhline(y=50, linestyle="--", color="red", label="Threshold")
    ax_vib.set_title("Vibration")
    ax_vib.legend()
    ax_vib.grid(True)

# ─────────────────────────────────────────────
# Start Live Animation
# ─────────────────────────────────────────────
ani = animation.FuncAnimation(fig, animate, interval=50, cache_frame_data=False)

try:
    plt.show()
finally:
    if not csvfile.closed:
        csvfile.close()
    if ser.is_open:
        ser.close()
    print(f"File saved: {filepath}")