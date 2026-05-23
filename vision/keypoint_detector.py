"""
人体关键点检测模块 - 基于 MediaPipe Pose Landmarker (0.10.x API)
输出统一 JSON 格式的关键点坐标
"""

import os
os.environ['GLOG_minloglevel'] = '2'

import cv2
from typing import Optional, Dict, List

import mediapipe as mp
import mediapipe.tasks as tasks
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarker, PoseLandmarkerOptions, PoseLandmarkerResult, PoseLandmark
from mediapipe.tasks.python.vision.core.image_processing_options import ImageProcessingOptions
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, 'pose_landmarker_lite.task')

# Pixel drawing connections for skeleton
POSE_CONNECTIONS = [
    (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_ELBOW),
    (PoseLandmark.LEFT_ELBOW, PoseLandmark.LEFT_SHOULDER),
    (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_HIP),
    (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_ELBOW),
    (PoseLandmark.RIGHT_ELBOW, PoseLandmark.RIGHT_SHOULDER),
    (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_HIP),
    (PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER),
    (PoseLandmark.LEFT_HIP, PoseLandmark.RIGHT_HIP),
    (PoseLandmark.LEFT_HIP, PoseLandmark.LEFT_KNEE),
    (PoseLandmark.LEFT_KNEE, PoseLandmark.LEFT_ANKLE),
    (PoseLandmark.RIGHT_HIP, PoseLandmark.RIGHT_KNEE),
    (PoseLandmark.RIGHT_KNEE, PoseLandmark.RIGHT_ANKLE),
    (PoseLandmark.NOSE, PoseLandmark.LEFT_EYE_INNER),
    (PoseLandmark.NOSE, PoseLandmark.RIGHT_EYE_INNER),
]

KEYPOINT_NAMES = {
    PoseLandmark.LEFT_WRIST: "left_wrist",
    PoseLandmark.LEFT_ELBOW: "left_elbow",
    PoseLandmark.LEFT_SHOULDER: "left_shoulder",
    PoseLandmark.RIGHT_WRIST: "right_wrist",
    PoseLandmark.RIGHT_ELBOW: "right_elbow",
    PoseLandmark.RIGHT_SHOULDER: "right_shoulder",
    PoseLandmark.NOSE: "nose",
}

COLORS = {
    "left_wrist": (0, 0, 255),
    "left_elbow": (0, 255, 0),
    "left_shoulder": (255, 0, 0),
    "right_wrist": (0, 255, 255),
    "right_elbow": (255, 255, 0),
    "right_shoulder": (255, 0, 255),
}


class KeypointDetector:
    """MediaPipe Pose Landmarker (0.10.x API)"""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"模型文件未找到: {model_path}\n"
                f"请从以下地址下载后放入 {os.path.dirname(model_path)}/ 目录:\n"
                f"https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                f"pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
            )

        options = PoseLandmarkerOptions(
            base_options=tasks.BaseOptions(model_asset_path=model_path),
            running_mode=tasks.vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = PoseLandmarker.create_from_options(options)

    def detect(self, frame) -> Optional[Dict[str, List[int]]]:
        """
        检测一帧中的人体关键点

        Returns:
            {
                "left_wrist": [x, y],
                "left_elbow": [x, y],
                ...
            }
            未检测到人时返回 None
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result: PoseLandmarkerResult = self.detector.detect(mp_image)

        if not result or not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return None

        landmarks = result.pose_landmarks[0]

        keypoints = {}
        for idx, name in KEYPOINT_NAMES.items():
            lm: NormalizedLandmark = landmarks[idx]
            keypoints[name] = [int(lm.x * w), int(lm.y * h)]

        return keypoints

    def draw_skeleton(self, frame, keypoints: Optional[Dict[str, List[int]]] = None):
        """在画面上绘制骨架点和连接线"""
        if keypoints is None:
            return

        for idx_a, idx_b in POSE_CONNECTIONS:
            name_a = KEYPOINT_NAMES.get(idx_a)
            name_b = KEYPOINT_NAMES.get(idx_b)
            if name_a and name_b and name_a in keypoints and name_b in keypoints:
                pt1 = tuple(keypoints[name_a])
                pt2 = tuple(keypoints[name_b])
                cv2.line(frame, pt1, pt2, (255, 255, 255), 2)

        for name, pt in keypoints.items():
            color = COLORS.get(name, (0, 255, 255))
            cv2.circle(frame, tuple(pt), 5, color, -1)
            cv2.putText(frame, name.replace("_", " ").title(), (pt[0] + 5, pt[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    def release(self):
        if hasattr(self, 'detector') and self.detector:
            self.detector = None


def main():
    """测试入口: 摄像头 + MediaPipe Pose Landmarker"""
    print("=" * 50)
    print("   关键点检测测试 - MediaPipe Pose Landmarker")
    print("=" * 50)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("摄像头打开失败")
        return

    detector = KeypointDetector()
    print("按 'q' 退出")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        keypoints = detector.detect(frame)
        if keypoints:
            detector.draw_skeleton(frame, keypoints)

        cv2.imshow("Keypoint Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    detector.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
