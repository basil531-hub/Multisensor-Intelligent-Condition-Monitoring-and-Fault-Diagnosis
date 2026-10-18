"""
Real-Time Frequency Analysis — DrillSense Extension (FFT Module)

This module performs real-time frequency domain analysis on:
- Vibration signal (piezo sensor)
- Current signal (ACS712)

Purpose:
Detect hidden fault frequencies in drill machine behavior using FFT.

Sampling:
- Arduino: ~20 Hz (50 ms loop)
- Nyquist limit: ~10 Hz usable frequency range

Key Features:
- Live FFT computation
- Dominant frequency detection
- Time + frequency domain visualization
- Serial data streaming from Arduino
"""

import serial
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# ─────────────────────────────────────────────
# Serial Configuration
# ─────────────────────────────────────────────
PORT = "COM9"
BAUD = 115200

# Effective sampling assumptions
FS = 20.0          # expected sample rate (Hz)
N_FFT = 128        # FFT window size (power of 2 recommended)
MAX_BUF = N_FFT * 4  # buffer for continuous streaming plots

# ─────────────────────────────────────────────
# Data Buffers (rolling window storage)
# ─────────────────────────────────────────────
vib_buf     = deque(maxlen=MAX_BUF)
current_buf = deque(maxlen=MAX_BUF)
timestamps  = deque(maxlen=MAX_BUF)

# Adaptive sampling rate estimation
last_sample_time = [time.time()]
measured_fs      = [FS]

# Exit control flag for threads
exit_flag = threading.Event()

# ─────────────────────────────────────────────
# Serial Data Parsing
# ─────────────────────────────────────────────
def parse_line(line: str):
    """
    Parse CSV line from Arduino.

    Expected format (8 columns):
    Timestamp, Current, Power, LM35, DHT_Temp, Humidity, Vib, Vib_Str

    Only current and vibration strength are used for FFT analysis.
    """
    parts = line.split(",")

    if len(parts) != 8:
        return None

    try:
        return {
            "timestamp": parts[0].strip(),
            "current": float(parts[1]),
            "vib_str": int(parts[7])
        }
    except:
        return None

# ─────────────────────────────────────────────
# Serial Reader Thread
# ─────────────────────────────────────────────
def serial_reader():
    """
    Continuously reads serial data from Arduino and updates buffers.
    Also estimates real sampling frequency dynamically.
    """
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
    except serial.SerialException as e:
        print(f"[ERROR] Cannot open {PORT}: {e}")
        exit_flag.set()
        return

    time.sleep(2)  # allow Arduino reset
    ser.flushInput()
    print(f"[INFO] Serial connected at {PORT}")

    while not exit_flag.is_set():
        try:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                data = parse_line(line)
                if data is None:
                    continue

                # ── Estimate real sampling frequency ──
                now = time.time()
                dt = now - last_sample_time[0]

                if 0.01 < dt < 0.5:
                    measured_fs[0] = 0.9 * measured_fs[0] + 0.1 * (1.0 / dt)

                last_sample_time[0] = now

                # ── Store signals for FFT ──
                vib_buf.append(data["vib_str"])
                current_buf.append(data["current"])
                timestamps.append(data["timestamp"])

            else:
                time.sleep(0.005)

        except Exception as e:
            print(f"[WARN] Serial error: {e}")

    ser.close()
    print("[INFO] Serial closed")

# Start background thread
threading.Thread(target=serial_reader, daemon=True).start()

# ─────────────────────────────────────────────
# FFT Processing Function
# ─────────────────────────────────────────────
def compute_fft(signal: np.ndarray, fs: float):
    """
    Compute single-sided FFT spectrum with windowing.

    Steps:
    - Remove DC offset
    - Apply Hanning window
    - Compute FFT
    - Convert to dB scale
    """
    n = len(signal)
    window = np.hanning(n)

    signal = signal - np.mean(signal)
    windowed = signal * window

    fft_vals = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(n, d=1/fs)

    amp = (2.0 / window.sum()) * np.abs(fft_vals)
    amp[0] /= 2  # DC correction
    amp_db = 20 * np.log10(amp + 1e-9)

    return freqs, amp_db

# ─────────────────────────────────────────────
# Dominant Frequency Detection
# ─────────────────────────────────────────────
def dominant_frequencies(freqs, amp_db, n=3):
    """
    Returns top-N frequency peaks (excluding DC).
    """
    idx = np.argsort(amp_db[1:])[::-1][:n] + 1
    return [(round(freqs[i], 3), round(amp_db[i], 1)) for i in idx]

# ─────────────────────────────────────────────
# Plot Setup (4-panel dashboard)
# ─────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle("Real-Time Frequency Analysis — DrillSense", fontsize=13)
plt.tight_layout(pad=3.5)

ax_vib_time = axes[0, 0]
ax_vib_freq = axes[0, 1]
ax_cur_time = axes[1, 0]
ax_cur_freq = axes[1, 1]

# ─────────────────────────────────────────────
# Peak annotation helper
# ─────────────────────────────────────────────
def annotate_peaks(ax, freqs, amp_db, color="red"):
    """
    Draws vertical markers for top frequency peaks.
    """
    peaks = dominant_frequencies(freqs, amp_db, n=3)
    lines = []

    for rank, (f, a) in enumerate(peaks):
        ax.axvline(f, color=color, linestyle="--", alpha=0.7 - rank*0.2)
        ax.text(f + 0.05,
                ax.get_ylim()[1] * 0.85 - rank * 8,
                f"{f:.2f} Hz\n{a:.1f} dB",
                fontsize=7, color=color)

    return lines

# ─────────────────────────────────────────────
# Main Animation Loop (Real-time update)
# ─────────────────────────────────────────────
def animate(frame):
    """
    Updates time-domain + frequency-domain plots every frame.
    """
    n_vib = len(vib_buf)
    n_cur = len(current_buf)

    # Wait until enough samples collected
    if n_vib < N_FFT or n_cur < N_FFT:
        fig.suptitle("Buffering data...", fontsize=13)
        return

    fs = max(1.0, measured_fs[0])

    vib = np.array(list(vib_buf)[-N_FFT:], dtype=float)
    cur = np.array(list(current_buf)[-N_FFT:], dtype=float)

    t = np.arange(len(vib)) / fs

    # ── Time domain: vibration ──
    ax_vib_time.cla()
    ax_vib_time.plot(t, vib, color="orange")
    ax_vib_time.set_title("Vibration (Time Domain)")

    # ── FFT: vibration ──
    ax_vib_freq.cla()
    vf, va = compute_fft(vib, fs)
    ax_vib_freq.plot(vf, va, color="orange")
    ax_vib_freq.set_title("Vibration (FFT)")

    annotate_peaks(ax_vib_freq, vf, va, "red")

    # ── Time domain: current ──
    ax_cur_time.cla()
    ax_cur_time.plot(t, cur, color="blue")
    ax_cur_time.set_title("Current (Time Domain)")

    # ── FFT: current ──
    ax_cur_freq.cla()
    cf, ca = compute_fft(cur, fs)
    ax_cur_freq.plot(cf, ca, color="blue")
    ax_cur_freq.set_title("Current (FFT)")

    annotate_peaks(ax_cur_freq, cf, ca, "navy")

    # ── Live title update ──
    fig.suptitle(
        f"Real-Time FFT | Fs={fs:.1f} Hz",
        fontsize=11
    )

# Start animation
ani = animation.FuncAnimation(fig, animate, interval=250, cache_frame_data=False)

print("[INFO] Running FFT analysis... Close window to stop.")

try:
    plt.show()
finally:
    exit_flag.set()
    print("[INFO] Program terminated cleanly.")