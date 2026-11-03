"""Full-grid fallback for the upright, front-facing 7x9 ChArUco board."""
from typing import Literal, Self

import cv2
import numpy as np
from numpy.typing import NDArray
from pydantic import model_validator
from skellytracker.core.data_primitives import Keypoints
from skellytracker.core.detectors.detection_context import DetectionContext
from skellytracker.core.detectors.detector_base_classes import KEYPOINT_DETECTOR_REGISTRY
from skellytracker.core.detectors.keypoint_detectors.charuco import CharucoDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.charuco.charuco_detector import (
    CharucoDetector,
    MINIMUM_CHARUCO_CORNERS_FOR_VISIBILITY,
)


class UprightCharucoDetectorConfig(CharucoDetectorConfig):
    detector_type: Literal["charuco_upright_checkerboard"] = "charuco_upright_checkerboard"

    @model_validator(mode="after")
    def require_7x9_board(self) -> Self:
        if (self.board.squares_x, self.board.squares_y) != (7, 9):
            raise ValueError("The upright checkerboard fallback requires a 7x9 board")
        return self


class UprightCharucoDetector(CharucoDetector):
    def detect(
        self,
        image: NDArray[np.uint8],
        context: DetectionContext | None = None,
    ) -> Keypoints:
        keypoints = super().detect(image, context)
        n_corners = self.config.board.n_corners
        if np.count_nonzero(keypoints.visibility[:n_corners] > 0) >= MINIMUM_CHARUCO_CORNERS_FOR_VISIBILITY:
            return keypoints

        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        found, corners = cv2.findChessboardCornersSB(
            grey, (6, 8), cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if not found:
            return keypoints

        grid = corners.reshape(8, 6, 2)
        # This mode assumes that both cameras see the printed front upright.
        if grid[0, :, 1].mean() > grid[-1, :, 1].mean():
            grid = grid[::-1, ::-1]
        if grid[:, 0, 0].mean() > grid[:, -1, 0].mean():
            raise ValueError("Board orientation is inconsistent with the upright fallback")

        keypoints.xyz[:n_corners, :2] = grid.reshape(n_corners, 2)
        keypoints.xyz[:n_corners, 2] = 0
        keypoints.visibility[:n_corners] = 1
        return keypoints


KEYPOINT_DETECTOR_REGISTRY["charuco_upright_checkerboard"] = UprightCharucoDetector
