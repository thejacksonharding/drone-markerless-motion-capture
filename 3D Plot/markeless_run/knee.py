from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks


csv = Path(r"C:\Users\astri\3D Plot\recordings\run1\ONNX_rtmpose_l_coco_wholebody\xyz_ONNX_rtmpose_l_coco_wholebody_labelled.csv")
df = pd.read_csv(csv)
fps = 30.0
split = 4000

H = df[["left_hip_x", "left_hip_y", "left_hip_z"]].to_numpy()
K = df[["left_knee_x", "left_knee_y", "left_knee_z"]].to_numpy()
A = df[["left_ankle_x", "left_ankle_y", "left_ankle_z"]].to_numpy()

u, v = H - K, A - K
dot = np.sum(u * v, axis=1)
norms = np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1)
angle_deg = 180 - np.degrees(np.arccos(np.clip(dot / norms, -1.0, 1.0)))

# Per-activity settings (tune each one separately)
segments = {
    "Walking": dict(start=0,     end=split,           prominence=20, min_dist_s=0.5, shift=-35, color="b"),
    "Jogging": dict(start=split, end=len(angle_deg),  prominence=20, min_dist_s=0.3, shift=-35, color="r"),
}

def gait_cycles(signal, fps, prominence, min_dist_s, shift):
    # 1. Fill gaps and smooth (this segment only)
    ang = pd.Series(signal).interpolate(limit_direction="both").to_numpy()
    b, a = butter(2, 6 / (fps / 2), btype="low")
    ang_f = filtfilt(b, a, ang)

    # 2. One big peak per stride
    peaks, _ = find_peaks(ang_f, prominence=prominence, distance=int(min_dist_s * fps))

    # 3. Cut strides, resample to 101 points, drop odd-length strides
    lengths = np.diff(peaks)
    keep = np.abs(lengths - np.median(lengths)) < 0.25 * np.median(lengths)
    cycles = []
    for s, e, ok in zip(peaks[:-1], peaks[1:], keep):
        if not ok:
            continue
        seg = ang_f[s:e + 1]
        cycles.append(np.interp(np.linspace(0, 100, 101),
                                np.linspace(0, 100, len(seg)), seg))
    cycles = np.array(cycles)

    # 4. Roll so both peaks are fully visible
    rolled = np.roll(cycles[:, :-1], shift, axis=1)
    cycles_shifted = np.concatenate([rolled, rolled[:, :1]], axis=1)
    return ang_f, peaks, cycles_shifted

#  RUN 
pct = np.arange(101)
results = {}

for name, p in segments.items():
    sig = angle_deg[p["start"]:p["end"]]
    ang_f, peaks, cyc = gait_cycles(sig, fps, p["prominence"], p["min_dist_s"], p["shift"])
    results[name] = cyc

    # Check peak detection (x-axis in original frame numbers)
    plt.figure(figsize=(12, 3))
    plt.plot(np.arange(p["start"], p["end"]), ang_f)
    plt.plot(peaks + p["start"], ang_f[peaks], "rx")
    plt.title(f"{name}: peak detection ({len(peaks)} peaks, {len(cyc)} strides kept)")
    plt.xlabel("Frame"); plt.ylabel("Knee flexion (deg)"); plt.show()

    # Cycles + mean +/- SD
    mean, sd = cyc.mean(0), cyc.std(0)
    plt.figure(figsize=(7, 4))
    plt.plot(pct, cyc.T, color="gray", alpha=0.3, lw=0.8)
    plt.plot(pct, mean, p["color"], lw=2, label=f"mean (n={len(cyc)})")
    plt.fill_between(pct, mean - sd, mean + sd, color=p["color"], alpha=0.2)
    plt.title(name)
    plt.xlabel("Shifted cycle (%)"); plt.ylabel("Knee flexion (deg)")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout(); plt.show()

# Walking vs jogging overlay
plt.figure(figsize=(7, 4))
for name, p in segments.items():
    cyc = results[name]
    mean, sd = cyc.mean(0), cyc.std(0)
    plt.plot(pct, mean, p["color"], lw=2, label=f"{name} (n={len(cyc)})")
    plt.fill_between(pct, mean - sd, mean + sd, color=p["color"], alpha=0.2)
plt.xlabel("Shifted cycle left knee (%)"); plt.ylabel("Knee flexion (deg)")
plt.legend(); plt.grid(alpha=0.3); plt.tight_layout(); plt.show()
# def cmc(curves):
#     """curves: (M, T). M waveforms (strides or methods), T time points."""
#     Y = np.asarray(curves, dtype=float)
#     M, T = Y.shape
#     num = np.sum((Y - Y.mean(axis=0)) ** 2) / (T * (M - 1))
#     den = np.sum((Y - Y.mean()) ** 2) / (M * T - 1)
#     r = 1 - num / den
#     return np.sqrt(r) if r >= 0 else np.nan

# for name, cyc in results.items():
#     print(f"{name}: within-trial CMC = {cmc(cyc):.3f} (n = {len(cyc)} strides)")