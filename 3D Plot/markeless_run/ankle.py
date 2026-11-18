from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fft import rfft, rfftfreq
from scipy.signal import find_peaks, butter, filtfilt

csv = Path(r"C:\Users\astri\3D Plot\recordings\run1\ONNX_rtmpose_l_coco_wholebody\xyz_ONNX_rtmpose_l_coco_wholebody_labelled.csv")
fps = 30
start, end = 0, 4000

df = pd.read_csv(csv)

# 1. Load data
Tl = df[["left_big_toe_x", "left_big_toe_y", "left_big_toe_z"]].to_numpy()
Kl = df[["left_knee_x", "left_knee_y", "left_knee_z"]].to_numpy()
Al = df[["right_ankle_x", "right_ankle_y", "right_ankle_z"]].to_numpy()  

# 2. CLEAN THE DATA: Replace rows where all coordinates are 0 with NaN, then interpolate
def clean(arr):
    arr = arr.astype(float).copy()
    arr[np.all(arr == 0, axis=1)] = np.nan
    return pd.DataFrame(arr).interpolate(limit_direction="both").to_numpy()

Tl, Kl, Al = clean(Tl), clean(Kl), clean(Al)

# 3. Calculate angle (now safe from dividing by zero)
u, v = Kl - Al, Tl - Al
dot = np.sum(u * v, axis=1)
norms = np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1)             
angle_deg = 90 - np.degrees(np.arccos(np.clip(dot / norms, -1.0, 1.0)))


segments = {
    "Walking": dict(start=0, end=4000, color="b"),
    "Jogging": dict(start=4000, end=8830, color="r"),
}
# 4. Filter and FFT (Notice we FFT 'angle_deg' which is now clean)
b, a = butter(N=2, Wn=1.5, fs=fps, btype='low')
angle_smooth = filtfilt(b, a, angle_deg)

# Remove DC offset
angle_smooth = angle_smooth - np.mean(angle_smooth)

# Calculate FFT
fft_values  = np.fft.rfft(angle_smooth)
frequencies = np.fft.rfftfreq(len(angle_smooth), d=1.0/fps)
mag = np.abs(fft_values) / len(angle_smooth)   

# 5. Plot
plt.figure(figsize=(12, 4))
plt.plot(frequencies, mag, color='tab:blue', lw=1.5) 
plt.xlim(0, 5)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.title("Knee flexion spectrum")
plt.grid(True)
plt.show()

def gait_cycles(signal, fps, prominence=5, min_dist_s=0.8):
    # We will pass the cleaned/smoothed signal into this function
    peaks, _ = find_peaks(signal, prominence=prominence, distance=int(min_dist_s * fps))

    lengths = np.diff(peaks)
    median_len = np.median(lengths) if len(lengths) > 0 else 0
    keep = np.abs(lengths - median_len) < 0.25 * median_len if median_len > 0 else []

    cycles = []
    for s, e, ok in zip(peaks[:-1], peaks[1:], keep):
        if not ok:
            continue
        seg = signal[s:e + 1]
        cycles.append(np.interp(np.linspace(0, 100, 101),
                                np.linspace(0, 100, len(seg)), seg))
    return signal, peaks, np.array(cycles)


# --- 6. Peak Detection Plots (Plots 2 & 3) ---
# We slice the smoothed angle for these plots
ang_f_walk, peaks_walk, cycles_walk = gait_cycles(angle_smooth[:4000], fps, prominence=10, min_dist_s=0.2)
ang_f_jog, peaks_jog, cycles_jog = gait_cycles(angle_smooth[4000:8830], fps, prominence=10, min_dist_s=0.2)

# Plot Walking Peaks
plt.figure(figsize=(12, 3))
frames2 = np.arange(0, len(ang_f_walk))
plt.plot(frames2, ang_f_walk, "-", color="b")
plt.plot(peaks_walk, ang_f_walk[peaks_walk], "rx")
plt.title(f"Walking Peak Detection ({len(peaks_walk)} peaks, {len(cycles_walk)} strides kept)")
plt.xlabel("Frame"); plt.ylabel("Ankle Flexion (deg)")
plt.grid(True)
plt.show()

# Plot Jogging Peaks
plt.figure(figsize=(12, 3))
frames = np.arange(4000, 4000 + len(ang_f_jog))
plt.plot(frames, ang_f_jog, "-", color="r")   
plt.plot(peaks_jog + 4000, ang_f_jog[peaks_jog], "rx")
plt.title(f"Jogging Peak Detection ({len(peaks_jog)} peaks, {len(cycles_jog)} strides kept)")
plt.xlabel("Frame"); plt.ylabel("Ankle Flexion (deg)")
plt.grid(True)
plt.show()


# --- 7. Mean Gait Cycle Plot (Plot 4) ---
plt.figure(figsize=(8, 5))
pct = np.linspace(0, 100, 101)

for name, params in segments.items():
    start, end = params["start"], params["end"]
    
    # Run gait cycles on the smoothed data segment
    _, _, cycles = gait_cycles(angle_smooth[start:end], fps, prominence=10, min_dist_s=0.2)
    print(f"{name}: {len(cycles)} cycles kept")

    if len(cycles) == 0:
        print(f"Warning: No valid cycles found for {name}")
        continue

    mean_cyc = cycles.mean(axis=0)
    std_cyc = cycles.std(axis=0)

    # Individual cycles (light)
    for c in cycles:
        plt.plot(pct, c, color=params["color"], alpha=0.15, lw=0.8)

    # Mean curve and ±1 SD band
    plt.plot(pct, mean_cyc, color=params["color"], lw=2.5, label=f"{name} mean")
    plt.fill_between(pct, mean_cyc - std_cyc, mean_cyc + std_cyc,
                     color=params["color"], alpha=0.2)

plt.axhline(0, color="k", lw=0.5)
plt.xlabel("Gait cycle (%)")
plt.ylabel("Ankle Flexion (deg)")
plt.title("Ankle angle over the gait cycle")
plt.xlim(0, 100)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()