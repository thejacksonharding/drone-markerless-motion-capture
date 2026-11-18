"""Chessboard-based intrinsic + extrinsic calibration with the Caliscope scripting API.

For when the GUI only offers ArUco/ChArUco for extrinsics but you only have a plain
chessboard. Written against caliscope 0.11.8 (the API names below were checked
against that release).

Steps the script performs:
  1. (optional) Intrinsic calibration of every camera from calibration/intrinsic/cam_N.mp4
     -> writes camera_array.toml
  2. Extrinsic calibration from calibration/extrinsic/cam_N.mp4 (synchronized videos where
     BOTH cameras see the chessboard at the same time)
  3. Quality report + saved capture volume + camera_array_aniposelib.toml

Run from the activated environment:
    python caliscope_chessboard_extrinsics.py
"""
from __future__ import annotations

from pathlib import Path

import cv2

from caliscope.api import (
    CameraArray,
    CameraDistance,
    Chessboard,
    ChessboardTracker,
    calibrate_extrinsics,
    calibrate_intrinsics,
    extract_image_points,
    extract_image_points_multicam,
)
from caliscope.reporting import print_extrinsic_report

# ============================== CONFIG ====================================
# Forward slashes avoid the "\U" unicode-escape SyntaxError on Windows.
PROJECT = Path("C:/Users/astri/3D Plot")

INTRINSIC_DIR = PROJECT / "calibration" / "intrinsic"   # cam_0.mp4, cam_1.mp4 (any timing)
EXTRINSIC_DIR = PROJECT / "calibration" / "extrinsic"   # cam_0.mp4, cam_1.mp4 (synchronized)
CAM_IDS = [0, 1]

# Chessboard INNER corners. Your GUI shows 7 x 9 squares -> 6 x 8 inner corners.
# The script tests both orientations on your video and keeps the one that detects more.
INNER_CORNERS = (8, 5)

# Edge length of one square in cm. Measure your print! Needed for metric scale.
# Set to None if you don't know it; then set BASELINE_M below instead.
SQUARE_SIZE_CM: float | None = 2

# Measured distance between the two camera centers (meters). Only used when
# SQUARE_SIZE_CM is None. Otherwise it's ignored.
BASELINE_M: float | None = 3.40

# True  = calibrate intrinsics here from INTRINSIC_DIR and write camera_array.toml.
# False = load an existing camera array from CAMERA_ARRAY_TOML.
REDO_INTRINSICS = True
CAMERA_ARRAY_TOML = PROJECT / "camera_array.toml"

INTRINSIC_FRAME_STEP = 5      # use every 5th frame; ~30 diverse frames are enough
EXTRINSIC_FRAME_STEP = 2      # every Nth synchronized frame
# Optional CSV with columns cam_id, frame_time (one row per frame per camera).
# None = infer from video metadata, which assumes both videos start together.
TIMESTAMPS_CSV: Path | None = None

# Let extrinsic calibration refine the intrinsics too. Reasonable when your intrinsic
# coverage was weak. Set False once you trust your intrinsics.
REFINE_INTRINSICS = True

OUTPUT_DIR = PROJECT / "chessboard_capture_volume"
# ==========================================================================


def video_for(folder: Path, cam_id: int) -> Path:
    path = folder / f"cam_{cam_id}.mp4"
    if not path.exists():
        raise FileNotFoundError(f"Missing video: {path}")
    return path


def pick_board_orientation(video: Path, inner: tuple[int, int], max_frames: int = 60) -> tuple[int, int]:
    """Return (rows, columns) of inner corners; try both orientations, keep the better one."""
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    cap = cv2.VideoCapture(str(video))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or max_frames
    step = max(1, total // max_frames)
    hits = {inner: 0, inner[::-1]: 0}
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            for rows, cols in hits:
                found, _ = cv2.findChessboardCorners(gray, (cols, rows), flags=flags)
                hits[(rows, cols)] += int(found)
        idx += 1
    cap.release()
    print(f"  chessboard detections in {video.name}: {hits}")
    best = max(hits, key=hits.get)
    if hits[best] == 0:
        raise RuntimeError(
            f"The chessboard was never detected in {video}. Check the inner-corner counts "
            f"({inner}) and that the whole board is visible and sharp in the video."
        )
    return best


def check_intrinsic_quality(cam_id: int, report) -> None:
    print(
        f"  cam {cam_id}: RMSE={report.rmse:.3f}px frames={report.frames_used} "
        f"coverage={report.coverage_fraction:.2f} edge={report.edge_coverage_fraction:.2f} "
        f"corner={report.corner_coverage_fraction:.2f} orientations={report.orientation_count}"
    )
    problems = []
    if report.coverage_fraction < 0.80:
        problems.append("coverage < 0.80")
    if report.edge_coverage_fraction < 0.75:
        problems.append("edge coverage < 0.75")
    if report.corner_coverage_fraction < 0.50:
        problems.append("corner coverage < 0.50")
    if not report.orientation_sufficient:
        problems.append("fewer than 4 board tilt directions")
    if problems:
        print(f"  WARNING cam {cam_id}: weak intrinsics ({', '.join(problems)}). "
              "Distortion/focal estimates may be unreliable.")


def main() -> None:
    intrinsic_videos = {c: video_for(INTRINSIC_DIR, c) for c in CAM_IDS}
    extrinsic_videos = {c: video_for(EXTRINSIC_DIR, c) for c in CAM_IDS}

    rows, cols = pick_board_orientation(extrinsic_videos[CAM_IDS[0]], INNER_CORNERS)
    print(f"Using inner corners: rows={rows}, columns={cols}")
    if rows % 2 == cols % 2:
        print(
            "WARNING: both inner-corner counts are even (or both odd). Such a board looks the "
            "same rotated 180 degrees, so the two cameras may label corners in opposite order. "
            "If the result looks wrong (huge error, flipped cameras), this is the likely cause; "
            "a board with one odd and one even corner count avoids it."
        )

    # ---------------- 1. intrinsics ----------------
    if REDO_INTRINSICS:
        print("Intrinsic calibration ...")
        cameras = CameraArray.from_video_metadata(intrinsic_videos)
        intrinsic_tracker = ChessboardTracker(Chessboard(rows=rows, columns=cols))  # unit spacing is fine
        for cam_id, video in intrinsic_videos.items():
            points = extract_image_points(video, cam_id, intrinsic_tracker, frame_step=INTRINSIC_FRAME_STEP)
            output = calibrate_intrinsics(points, cameras[cam_id])
            cameras[cam_id] = output.camera
            check_intrinsic_quality(cam_id, output.report)
        CAMERA_ARRAY_TOML.parent.mkdir(parents=True, exist_ok=True)
        cameras.to_toml(CAMERA_ARRAY_TOML)
        print(f"  saved intrinsics to {CAMERA_ARRAY_TOML}")
    else:
        cameras = CameraArray.from_toml(CAMERA_ARRAY_TOML)

    # ---------------- 2. extrinsics ----------------
    print("Extrinsic calibration ...")
    extrinsic_tracker = ChessboardTracker(Chessboard(rows=rows, columns=cols, square_size_cm=SQUARE_SIZE_CM))
    image_points = extract_image_points_multicam(
        extrinsic_videos,
        extrinsic_tracker,
        frame_step=EXTRINSIC_FRAME_STEP,
        timestamps=TIMESTAMPS_CSV,
    )
    run = calibrate_extrinsics(
        image_points,
        cameras,
        constraints=None,
        refine_intrinsics=REFINE_INTRINSICS,
    )
    volume = run.capture_volume

    if SQUARE_SIZE_CM is None:
        if BASELINE_M is None:
            print("No square size or baseline given: the result is in arbitrary units.")
        else:
            volume = volume.scaled(CameraDistance(cam_a=CAM_IDS[0], cam_b=CAM_IDS[1], meters=BASELINE_M))

    # ---------------- 3. report and save ----------------
    print_extrinsic_report(volume)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    volume.save(OUTPUT_DIR)
    volume.camera_array.to_aniposelib_toml(OUTPUT_DIR.parent / "camera_array_aniposelib.toml")
    print(f"Saved capture volume to {OUTPUT_DIR}")
    print("Check: reprojection error is small AND the camera layout/distance matches reality.")


if __name__ == "__main__":
    main()