from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

csv = Path(r"C:\Users\astri\3D Plot\recordings\run1\ONNX_rtmpose_l_coco_wholebody\xyz_ONNX_rtmpose_l_coco_wholebody_labelled.csv")
df = pd.read_csv(csv)

Hl = df[["left_hip_x", "left_hip_y", "left_hip_z"]].to_numpy()
Kl = df[["left_knee_x", "left_knee_y", "left_knee_z"]].to_numpy()
Al = df[["left_ankle_x", "left_ankle_y", "left_ankle_z"]].to_numpy()
Heel_l = df[["left_heel_x", "left_heel_y", "left_heel_z"]].to_numpy()
Hr = df[["right_hip_x", "right_hip_y", "right_hip_z"]].to_numpy()
Kr = df[["right_knee_x", "right_knee_y", "right_knee_z"]].to_numpy()
Ar = df[["right_ankle_x", "right_ankle_y", "right_ankle_z"]].to_numpy()
Heel_r = df[["right_heel_x", "right_heel_y", "right_heel_z"]].to_numpy()
thigh_l = np.linalg.norm(Hl - Kl)
thigh_r = np.linalg.norm(Hr - Kr)
shank_l = np.linalg.norm(Kl - Al)
shank_r = np.linalg.norm(Kr - Ar)
ankle_l = np.linalg.norm(Al - Heel_l)
ankle_r = np.linalg.norm(Ar - Heel_r)
print("Left thigh length:", np.mean(thigh_l), "m")
print("Right thigh length:", np.mean(thigh_r), "m")
print("Left shank length:", np.mean(shank_l), "m")
print("Right shank length:", np.mean(shank_r), "m")
print("Left ankle length:", np.mean(ankle_l), "m")
print("Right ankle length:", np.mean(ankle_r), "m")
