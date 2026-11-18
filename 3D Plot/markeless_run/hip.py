from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter


csv = Path(r"C:\Users\astri\3D Plot\recordings\run1\ONNX_rtmpose_l_coco_wholebody\xyz_ONNX_rtmpose_l_coco_wholebody_labelled.csv")
fps = 30
start, end = 0, 4000

df = pd.read_csv(csv)

Hl = df[["left_hip_x", "left_hip_y", "left_hip_z"]].to_numpy()
Hr = df[["right_hip_x", "right_hip_y", "right_hip_z"]].to_numpy()
Kl = df[["left_knee_x", "left_knee_y", "left_knee_z"]].to_numpy()
Kr = df[["right_knee_x", "right_knee_y", "right_knee_z"]].to_numpy()    
print("net x displacement while walking:", Hl[4000-1, 0] - Hl[300, 0])
# def clean(arr):
#     arr = arr.astype(float).copy()
#     arr[np.all(arr == 0, axis=1)] = np.nan          # failed detections stored as 0
#     return pd.DataFrame(arr).interpolate(limit_direction="both").to_numpy()

# Hl, Hr, Kl = clean(Hl), clean(Hr), clean(Kl)
# Kr = clean(Kr)


# def unit(v):
#     n = np.linalg.norm(v, axis=1, keepdims=True)
#     out = np.full_like(v, np.nan)
#     np.divide(v, n, out=out, where=n > 1e-9)   # NaN instead of a warning where n == 0
#     return out

def hip_flexion(H, Hl, Hr, K, g=(0, -1, 0)):
    """
    H      : (n,3) hip of the leg being analysed (Hl for left leg, Hr for right leg)
    Hl, Hr : (n,3) left and right hip centres (define the pelvis frame)
    K      : (n,3) knee of the same leg
    g      : global 'up' vector in YOUR coordinate system
    """
    g = np.asarray(g, dtype=float)

    # femur: unit vector hip -> knee
    f = K - H
    f /= np.linalg.norm(f, axis=1, keepdims=True)

    # lateral axis, perpendicular to the sagittal plane (left hip -> right hip)
    l = Hl-Hr
    l /= np.linalg.norm(l, axis=1, keepdims=True)

    # superior axis: project g onto the plane perpendicular to l, then normalise
    p = g - np.sum(g * l, axis=1, keepdims=True) * l
    p /= np.linalg.norm(p, axis=1, keepdims=True)

    # anterior axis
    a = np.cross(p, l, axis=1)

    # sagittal-plane angle
    theta = np.arctan2(np.sum(f * a, axis=1), -np.sum(f * p, axis=1))
    return np.degrees(theta)





hip_angle_left = hip_flexion(Hl, Hl, Hr, Kl)       # left hip flexion
hip_angle_right = hip_flexion(Hr, Hl, Hr, Kr)




def gait_cycles(signal, fps, prominence=5, min_dist_s=0.8):
    # 1. Fill gaps and smooth (this segment only)
    # ang = pd.Series(signal).interpolate(limit_direction="both").to_numpy()
    # ang_f = savgol_filter(ang, 11, 3)

    # 2. One big peak per stride
    peaks, _ = find_peaks(signal, prominence=prominence, distance=int(min_dist_s * fps))

    # 3. Cut strides, resample to 101 points, drop odd-length strides
    lengths = np.diff(peaks)
    keep = np.abs(lengths - np.median(lengths)) < 0.25 * np.median(lengths)
    cycles = []
    for s, e, ok in zip(peaks[:-1], peaks[1:], keep):
        if not ok:
            continue
        seg = signal[s:e + 1]
        cycles.append(np.interp(np.linspace(0, 100, 101),
                                np.linspace(0, 100, len(seg)), seg))
    cycles = np.array(cycles)
    return signal, peaks, cycles
pct = np.linspace(0, 100, 101)
segments = {
    "Walking": dict(start=0, end=4000, color="b"),
    "Jogging": dict(start=4000, end=8830, color="r"),
}

plt.figure(figsize=(8, 5))

for name, params in segments.items():
    start, end = params["start"], params["end"]
    ang_f, peaks, cycles = gait_cycles(hip_angle_left[start:end], fps)
    print(f"{name}: {len(peaks)} peaks -> {len(cycles)} cycles kept")

    mean_cyc = cycles.mean(axis=0)
    std_cyc = cycles.std(axis=0)

    # Individual cycles (light, same color as the segment)
    for c in cycles:
        plt.plot(pct, c, color=params["color"], alpha=0.15, lw=0.8)

    # Mean curve and ±1 SD band
    plt.plot(pct, mean_cyc, color=params["color"], lw=2.5, label=f"{name} mean")
    plt.fill_between(pct, mean_cyc - std_cyc, mean_cyc + std_cyc,
                     color=params["color"], alpha=0.2)

plt.axhline(0, color="k", lw=0.5)
plt.xlabel("Gait cycle (%)")
plt.ylabel("Left hip flexion (deg)")
plt.title("Left hip angle over the gait cycle")
plt.xlim(0, 100)
plt.legend()
plt.tight_layout()
plt.show()
# 3. Time-normalize each cycle to 101 points (0-100 %)


mean_cyc = cycles.mean(axis=0)
std_cyc = cycles.std(axis=0)

# plt.figure(figsize=(12, 3))
# frames2 = np.arange(0, 4000,1)
# plt.plot(frames2, hip_angle_left[0:4000])

# ang_f2, peaks2, cycles2 = gait_cycles(hip_angle_left[4000:], fps, prominence=8, min_dist_s=0.8)

# plt.figure(figsize=(12, 3))
# frames = np.arange(4000, 4000 + len(ang_f2))
# plt.plot(frames, ang_f2, "-")   
# plt.plot(peaks2 + 4000, ang_f2[peaks2], "rx")
# plt.title(f"peak detection ({len(peaks2)} peaks, {len(cycles2)} strides kept)")
# plt.xlabel("Frame"); plt.ylabel("Knee flexion (deg)"); plt.show()




# 4. Plot
plt.figure(figsize=(8, 5))
for c in cycles:
    plt.plot(pct, c, color="gray", alpha=0.25, lw=0.8)
plt.plot(pct, mean_cyc, color="tab:blue", lw=2.5, label="Mean")
plt.fill_between(pct, mean_cyc - std_cyc, mean_cyc + std_cyc,
                 color="tab:blue", alpha=0.2, label="± 1 SD")
plt.axhline(0, color="k", lw=0.5)
plt.xlabel("Gait cycle (%)")
plt.ylabel("Left hip flexion (deg)")
plt.title("Left hip angle over the gait cycle walking")
plt.xlim(0, 100)
plt.legend()
plt.tight_layout()
plt.show()

