"""
ADAMS Eye Detector
==================
Wraps MediaPipe's Face Landmarker Tasks API to compute per-frame Eye Aspect
Ratio (EAR) values, detect sustained drowsiness, and identify driver
distraction via head-pose yaw estimation.

Authors : ADAMS Team
Version : 2.1.0

Algorithm references
--------------------
- EAR: Soukupová & Čech (2016) — "Real-Time Eye Blink Detection using Facial
  Landmarks".  EAR = (‖p2−p6‖ + ‖p3−p5‖) / (2 · ‖p1−p4‖)
- Head pose: yaw angle extracted from the 4×4 facial transformation matrix
  returned by MediaPipe's FaceLandmarker.  A yaw beyond ±YAW_THRESHOLD
  degrees indicates the driver is looking significantly off-road.
"""

import logging
import math
import os

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("adams.eye_detector")

# ---------------------------------------------------------------------------
# EAR constants
# ---------------------------------------------------------------------------
EAR_THRESHOLD: float = 0.25          # below this → eye is "closed"
CLOSED_FRAMES_THRESHOLD: int = 10    # consecutive closed frames → drowsy
EAR_NORMALISER: float = 0.35         # EAR value treated as "fully open"

# MediaPipe Face Mesh landmark indices for the six EAR control points.
# Order: [left_corner, upper1, upper2, right_corner, lower2, lower1]
LEFT_EYE_INDICES:  tuple[int, ...] = (362, 385, 387, 263, 373, 380)
RIGHT_EYE_INDICES: tuple[int, ...] = (33,  160, 158, 133, 153, 144)

# ---------------------------------------------------------------------------
# Distraction / head-pose constants
# ---------------------------------------------------------------------------
# Yaw angle (left/right head rotation) beyond this threshold → distracted.
# ±20° is a practical road-safety threshold; tighten to ±15° for stricter detection.
YAW_THRESHOLD_DEG: float = 20.0
DISTRACTED_FRAMES_THRESHOLD: int = 8   # frames of off-road gaze before flagging

# HUD colours
_GREEN  = (0, 255, 0)
_YELLOW = (0, 200, 255)
_RED    = (0, 0, 255)
_BLACK  = (0, 0, 0)


# ---------------------------------------------------------------------------
# EyeDetector
# ---------------------------------------------------------------------------
class EyeDetector:
    """
    Detects eye landmarks, computes EAR, identifies drowsiness, and estimates
    head-pose yaw to flag driver distraction.

    Parameters
    ----------
    model_path : str, optional
        Absolute path to ``face_landmarker.task``.  Defaults to looking for
        the file in the same directory as this module.
    ear_threshold : float
        EAR below which the eye is considered closed.
    closed_frames_threshold : int
        Consecutive closed-eye frames required before drowsiness is flagged.
    yaw_threshold_deg : float
        Head yaw angle (°) beyond which the driver is considered distracted.
    distracted_frames_threshold : int
        Consecutive off-road-gaze frames required before distraction is flagged.
    """

    def __init__(
        self,
        model_path: str | None = None,
        ear_threshold: float = EAR_THRESHOLD,
        closed_frames_threshold: int = CLOSED_FRAMES_THRESHOLD,
        yaw_threshold_deg: float = YAW_THRESHOLD_DEG,
        distracted_frames_threshold: int = DISTRACTED_FRAMES_THRESHOLD,
    ) -> None:
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "face_landmarker.task",
            )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Face landmarker model not found at '{model_path}'. "
                "Download it from https://developers.google.com/mediapipe/solutions/vision/face_landmarker"
            )

        self.ear_threshold = ear_threshold
        self.closed_frames_threshold = closed_frames_threshold
        self.yaw_threshold_deg = yaw_threshold_deg
        self.distracted_frames_threshold = distracted_frames_threshold

        self._closed_frame_count: int = 0
        self._distracted_frame_count: int = 0

        # output_facial_transformation_matrixes=True is required for yaw extraction
        base_opts = python.BaseOptions(model_asset_path=model_path)
        opts = vision.FaceLandmarkerOptions(
            base_options=base_opts,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
        )
        self._detector = vision.FaceLandmarker.create_from_options(opts)
        logger.info(
            "EyeDetector ready — EAR threshold=%.2f, yaw threshold=%.1f°",
            self.ear_threshold,
            self.yaw_threshold_deg,
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def analyze(self, frame: np.ndarray) -> dict:
        """
        Analyse a BGR video frame and return eye-state and distraction metrics.

        Parameters
        ----------
        frame : np.ndarray
            Single BGR image from OpenCV's ``VideoCapture.read()``.

        Returns
        -------
        dict with keys:
            eye_opening     (float) : normalised openness in [0.0, 1.0].
            is_drowsy       (bool)  : True after ``closed_frames_threshold``
                                      consecutive closed-eye frames.
            is_distracted   (bool)  : True after ``distracted_frames_threshold``
                                      consecutive off-road-gaze frames.
            yaw_deg         (float) : head yaw angle in degrees (+left, −right).
            ear_value       (float) : raw average EAR.
            face_detected   (bool)  : False if no face was found.
        """
        rgb = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
        )
        result = self._detector.detect(rgb)

        if not result.face_landmarks:
            self._closed_frame_count = 0
            self._distracted_frame_count = 0
            return {
                "eye_opening":   1.0,
                "is_drowsy":     False,
                "is_distracted": False,
                "yaw_deg":       0.0,
                "ear_value":     0.30,
                "face_detected": False,
            }

        landmarks = result.face_landmarks[0]

        # --- EAR / drowsiness ---
        left_ear  = self._compute_ear(landmarks, LEFT_EYE_INDICES)
        right_ear = self._compute_ear(landmarks, RIGHT_EYE_INDICES)
        avg_ear   = (left_ear + right_ear) / 2.0

        if avg_ear < self.ear_threshold:
            self._closed_frame_count += 1
        else:
            self._closed_frame_count = 0

        is_drowsy   = self._closed_frame_count >= self.closed_frames_threshold
        eye_opening = round(min(avg_ear / EAR_NORMALISER, 1.0), 2)

        # --- Head-pose yaw / distraction ---
        yaw_deg = 0.0
        if result.facial_transformation_matrixes:
            yaw_deg = self._extract_yaw_deg(result.facial_transformation_matrixes[0])

        if abs(yaw_deg) > self.yaw_threshold_deg:
            self._distracted_frame_count += 1
        else:
            self._distracted_frame_count = 0

        is_distracted = self._distracted_frame_count >= self.distracted_frames_threshold

        logger.debug(
            "EAR=%.3f closed=%d drowsy=%s | yaw=%.1f° distracted_frames=%d distracted=%s",
            avg_ear, self._closed_frame_count, is_drowsy,
            yaw_deg, self._distracted_frame_count, is_distracted,
        )

        return {
            "eye_opening":   eye_opening,
            "is_drowsy":     is_drowsy,
            "is_distracted": is_distracted,
            "yaw_deg":       round(yaw_deg, 1),
            "ear_value":     round(avg_ear, 3),
            "face_detected": True,
        }

    def draw_overlay(self, frame: np.ndarray, eye_data: dict) -> np.ndarray:
        """
        Render a HUD on *frame* (returns an annotated copy).

        Drowsiness → red border + centre alert text.
        Distraction → yellow border + centre alert text.
        Both active  → red takes priority for the border.

        Parameters
        ----------
        frame : np.ndarray
            BGR frame from the capture loop.
        eye_data : dict
            Output of ``analyze()``.

        Returns
        -------
        np.ndarray
            Annotated BGR frame.
        """
        frame = frame.copy()
        h, w = frame.shape[:2]
        is_drowsy     = eye_data["is_drowsy"]
        is_distracted = eye_data.get("is_distracted", False)

        # Choose accent colour for EAR readout
        if is_drowsy:
            accent = _RED
        elif is_distracted:
            accent = _YELLOW
        else:
            accent = _GREEN

        # Semi-transparent header bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), _BLACK, -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        cv2.putText(
            frame, "ADAMS SYSTEM: ACTIVE | AI BRAIN: ONLINE",
            (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, _GREEN, 1, cv2.LINE_AA,
        )

        # EAR + yaw readout
        cv2.putText(
            frame, f"EAR: {eye_data['ear_value']:.2f}",
            (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, accent, 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Yaw: {eye_data.get('yaw_deg', 0.0):+.1f}\u00b0",
            (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.65, accent, 2, cv2.LINE_AA,
        )

        # Danger overlays (drowsiness takes priority)
        if is_drowsy:
            cv2.rectangle(frame, (0, 0), (w, h), _RED, 10)
            cv2.putText(
                frame, "DROWSINESS ALERT",
                (w // 2 - 140, h // 2), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, _RED, 3, cv2.LINE_AA,
            )
        elif is_distracted:
            cv2.rectangle(frame, (0, 0), (w, h), _YELLOW, 10)
            cv2.putText(
                frame, "DISTRACTION ALERT",
                (w // 2 - 145, h // 2), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, _YELLOW, 3, cv2.LINE_AA,
            )

        return frame

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_ear(landmarks, indices: tuple[int, ...]) -> float:
        """
        Compute the Eye Aspect Ratio for a single eye.

        Parameters
        ----------
        landmarks : list
            MediaPipe NormalizedLandmark list for one face.
        indices : tuple[int, ...]
            Six landmark indices in order:
            [left_corner, upper1, upper2, right_corner, lower2, lower1]

        Returns
        -------
        float
            EAR value (0.0 if the horizontal span is zero).
        """
        pts = np.array(
            [(landmarks[i].x, landmarks[i].y) for i in indices],
            dtype=np.float32,
        )
        vert_a = np.linalg.norm(pts[1] - pts[5])
        vert_b = np.linalg.norm(pts[2] - pts[4])
        horiz  = np.linalg.norm(pts[0] - pts[3])
        return float((vert_a + vert_b) / (2.0 * horiz)) if horiz > 0 else 0.0

   
    def _extract_yaw_deg(self, matrix):
        """Extracts yaw (side-to-side head turn) from the transformation matrix."""
        try:
            # We use 'matrix' here, which was passed in. 
            # 'self' is required by Python classes even if we don't call a self.variable inside.
            m = np.array(matrix.data).reshape(4, 4)

            # Yaw calculation
            yaw_rad = np.arctan2(m[0, 2], m[2, 2])
            return float(np.degrees(yaw_rad))
        except Exception as e:
            print(f"Yaw extraction error: {e}")
            return 0.0