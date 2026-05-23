"""
内关穴定位系统 - 开发调试工具
显示 OpenCV 详细可视化画面（骨架、关键点标注、角度信息）
仅供算法调试使用，正式演示请用 ui/main_ui.py
"""

import sys
import os
import json
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
from vision.keypoint_detector import KeypointDetector
from rules.acupoint_calculator import calculate_neiguan_both

OUTPUT_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'ui', 'output.json')
)


def write_output(acupoint_data: dict):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(acupoint_data, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 55)
    print("    内关穴定位系统 - 开发调试工具")
    print("    显示详细可视化信息，用于算法调试")
    print("=" * 55)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("摄像头打开失败")
        return

    detector = KeypointDetector()
    print("按 'q' 退出")
    print(f"输出文件: {OUTPUT_FILE}")
    print("-" * 55)

    last_output_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        keypoints = detector.detect(frame)

        if keypoints:
            detector.draw_skeleton(frame, keypoints)

            results = calculate_neiguan_both(keypoints)
            for side, label, color in [("left", "Neiguan L", (0, 0, 255)),
                                       ("right", "Neiguan R", (0, 255, 255))]:
                r = results.get(side)
                if r:
                    nx, ny = r["x"], r["y"]
                    cv2.circle(frame, (nx, ny), 10, color, -1)
                    cv2.circle(frame, (nx, ny), 14, color, 2)
                    cv2.putText(frame, label, (nx + 15, ny),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.putText(frame, f"({nx}, {ny})", (nx + 15, ny + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

                    wrist = keypoints.get(f"{side}_wrist")
                    elbow = keypoints.get(f"{side}_elbow")
                    if wrist and elbow:
                        cv2.line(frame, tuple(wrist), tuple(elbow), color, 2)

            best = results.get("right") or results.get("left")
            if best:
                now = time.time()
                if now - last_output_time > 0.1:
                    last_output_time = now
                    write_output(best)
        else:
            cv2.putText(frame, "No person detected", (w // 2 - 120, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.putText(frame, "Acupoint Localization - Neiguan (Debug)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Acupoint Localization [Debug]", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    detector.release()
    cv2.destroyAllWindows()
    print("\n程序已退出")


if __name__ == "__main__":
    main()
