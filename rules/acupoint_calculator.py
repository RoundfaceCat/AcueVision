"""
穴位计算规则模块 - 基于同身寸法
将中医穴位定位规则转换为数学公式
"""

import math
from typing import Dict, List, Optional


def calculate_neiguan(keypoints: Dict[str, List[int]], side: str = "left") -> Optional[Dict]:
    """
    计算内关穴位置

    中医规则:
        腕横纹至肘横纹 = 12寸
        内关穴: 腕横纹上2寸, 两筋之间

    数学公式:
        1寸 = (肘到腕距离) / 12
        内关 = 腕 + (肘 - 腕) * (2 / 12)

    Args:
        keypoints: 关键点字典, 需包含 wrist 和 elbow
        side: "left" 或 "right"

    Returns:
        {
            "name": "内关",
            "x": int,
            "y": int,
            "confidence": float
        }
        如果关键点缺失则返回 None
    """
    wrist_key = f"{side}_wrist"
    elbow_key = f"{side}_elbow"

    if wrist_key not in keypoints or elbow_key not in keypoints:
        return None

    wrist = keypoints[wrist_key]
    elbow = keypoints[elbow_key]

    if wrist is None or elbow is None:
        return None

    wrist_x, wrist_y = wrist
    elbow_x, elbow_y = elbow

    dx = elbow_x - wrist_x
    dy = elbow_y - wrist_y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    if distance < 1:
        return None

    ratio = 2.0 / 12.0

    neiguan_x = int(wrist_x + dx * ratio)
    neiguan_y = int(wrist_y + dy * ratio)

    confidence = min(distance / 200.0, 1.0)
    confidence = round(confidence, 2)

    return {
        "name": "内关",
        "x": neiguan_x,
        "y": neiguan_y,
        "confidence": confidence,
    }


def calculate_neiguan_both(keypoints: Dict[str, List[int]]) -> Dict[str, Optional[Dict]]:
    """
    同时计算左右两侧内关穴

    Returns:
        {
            "left": { "name": "内关(左)", "x": ..., "y": ..., "confidence": ... } or None,
            "right": { "name": "内关(右)", "x": ..., "y": ..., "confidence": ... } or None,
        }
    """
    return {
        "left": calculate_neiguan(keypoints, side="left"),
        "right": calculate_neiguan(keypoints, side="right"),
    }


def select_best_arm(keypoints: Dict[str, List[int]]) -> str:
    """
    选择置信度更高的一侧手臂 (用于优先定位)

    Returns:
        "left" 或 "right"
    """
    left_ok = (keypoints.get("left_wrist") is not None
               and keypoints.get("left_elbow") is not None)
    right_ok = (keypoints.get("right_wrist") is not None
                and keypoints.get("right_elbow") is not None)

    if left_ok and not right_ok:
        return "left"
    if right_ok and not left_ok:
        return "right"
    return "left"
