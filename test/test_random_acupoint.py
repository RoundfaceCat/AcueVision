"""
穴位坐标随机测试脚本 - 模拟算法输出
每隔 0.5 秒随机修改 ui/output.json 中的坐标，用于测试 UI 红点动态移动
"""

import json
import os
import time
import random

# ===== 关键：使用绝对路径，确保写入正确位置 =====
# 如果你的项目路径不是 C:\Users\JERRY\acupoint-system，请修改下面的路径
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ui",
    "output.json"
)

OUTPUT_FILE = os.path.normpath(OUTPUT_FILE)
# 摄像头画面尺寸（与 UI 一致）
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 只输出内关穴
ACUPOINT_NAMES = ["内关"]


def generate_random_position():
    """生成随机穴位坐标"""
    x = random.randint(50, FRAME_WIDTH - 50)
    y = random.randint(50, FRAME_HEIGHT - 50)
    return x, y


def update_output_json(x: int, y: int, name: str):
    """更新 output.json（模拟算法输出）"""
    data = {
        "name": name,
        "x": x,
        "y": y,
        "confidence": round(random.uniform(0.7, 0.99), 2)
    }
    # 确保目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"已更新：{name} -> x={x}, y={y}")


def main():
    """主函数"""
    print(f"测试脚本启动，目标文件：{OUTPUT_FILE}")
    print(f"画面尺寸：{FRAME_WIDTH}x{FRAME_HEIGHT}")
    print("按 Ctrl+C 停止...\n")

    try:
        count = 0
        while True:
            x, y = generate_random_position()
            name = random.choice(ACUPOINT_NAMES)
            update_output_json(x, y, name)
            count += 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n测试结束，共更新 {count} 次")


if __name__ == "__main__":
    main()