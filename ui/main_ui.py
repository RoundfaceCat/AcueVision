"""
UI 主程序 - 摄像头显示 + 实时穴位检测 + 红点叠加 + 穴位信息面板

数据流:
    摄像头 → KeypointDetector → calculate_neiguan → 画红点 + info面板
                                                      ↓
                                                  output.json (供 ESP32 读取)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vision.keypoint_detector import KeypointDetector
from rules.acupoint_calculator import calculate_neiguan_both


OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output.json")


def write_output(data: dict):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class CameraPanel:
    def __init__(self, parent, width=640, height=480):
        self.parent = parent
        self.width = width
        self.height = height

        self.frame = ttk.Frame(parent)
        self.camera_label = ttk.Label(self.frame)
        self.camera_label.pack(fill=tk.BOTH, expand=True)

        self.cap = None
        self.is_running = False
        self.acupoint_left = None
        self.acupoint_right = None
        self.detector = KeypointDetector()
        self.frame_count = 0
        self.esp32_ctrl = None

    def set_esp32(self, ctrl):
        self.esp32_ctrl = ctrl

    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("无法打开摄像头")
        self.is_running = True
        self._update_frame()

    def stop_camera(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _update_frame(self):
        if self.is_running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.frame_count += 1

                keypoints = self.detector.detect(frame)
                found = False
                self.acupoint_left = None
                self.acupoint_right = None

                if keypoints:
                    results = calculate_neiguan_both(keypoints)
                    for side, label, color in [("left", "Neiguan L", (0, 0, 255)),
                                                ("right", "Neiguan R", (0, 255, 255))]:
                        r = results.get(side)
                        if r:
                            cv2.circle(frame, (r["x"], r["y"]), 8, color, -1)
                            cv2.circle(frame, (r["x"], r["y"]), 12, color, 2)
                            cv2.putText(frame, label, (r["x"] + 15, r["y"]),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            if side == "left":
                                self.acupoint_left = r
                            else:
                                self.acupoint_right = r
                            found = True

                    if self.acupoint_right:
                        best = self.acupoint_right
                    elif self.acupoint_left:
                        best = self.acupoint_left
                    else:
                        best = None

                    if best and self.frame_count % 5 == 0:
                        write_output(best)
                        if self.esp32_ctrl:
                            ah = int((best["x"] / self.width) * 180)
                            av = int((1.0 - best["y"] / self.height) * 180)
                            ah = max(0, min(180, ah))
                            av = max(0, min(180, av))
                            self.esp32_ctrl.send_command(ah, av, 1)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(img)
                self.camera_label.configure(image=img_tk)
                self.camera_label.image = img_tk

                if found:
                    self.parent.event_generate("<<AcupointUpdated>>", when="tail")

        if self.is_running:
            self.parent.after(30, self._update_frame)


class AcupointInfoPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=20)
        self.db_path = os.path.join(os.path.dirname(__file__), "acupoints_db.json")

        ttk.Label(self.frame, text="穴位定位", font=("Microsoft YaHei UI", 16, "bold")).pack(pady=(0, 20))
        ttk.Separator(self.frame, orient='horizontal').pack(fill=tk.X, pady=10)

        name_frame = ttk.Frame(self.frame)
        ttk.Label(name_frame, text="穴位名称：", font=("Microsoft YaHei UI", 12)).pack(side=tk.LEFT)
        self.name_value = ttk.Label(name_frame, text="内关", font=("Microsoft YaHei UI", 12, "bold"), foreground="#d32f2f")
        self.name_value.pack(side=tk.LEFT)
        name_frame.pack(pady=15, anchor=tk.W)

        # 左右双侧坐标
        coord_frame = ttk.Frame(self.frame)
        ttk.Label(coord_frame, text="左侧坐标：", font=("Microsoft YaHei UI", 11)).pack(side=tk.LEFT)
        self.coord_left = ttk.Label(coord_frame, text="--", font=("Microsoft YaHei UI", 11))
        self.coord_left.pack(side=tk.LEFT)
        coord_frame.pack(pady=5, anchor=tk.W)

        coord_frame_r = ttk.Frame(self.frame)
        ttk.Label(coord_frame_r, text="右侧坐标：", font=("Microsoft YaHei UI", 11)).pack(side=tk.LEFT)
        self.coord_right = ttk.Label(coord_frame_r, text="--", font=("Microsoft YaHei UI", 11))
        self.coord_right.pack(side=tk.LEFT)
        coord_frame_r.pack(pady=5, anchor=tk.W)

        pos_frame = ttk.Frame(self.frame)
        ttk.Label(pos_frame, text="位置：", font=("Microsoft YaHei UI", 12)).pack(side=tk.LEFT)
        self.pos_value = ttk.Label(pos_frame, text="前臂掌侧，腕横纹上 2 寸", font=("Microsoft YaHei UI", 11))
        self.pos_value.pack(side=tk.LEFT)
        pos_frame.pack(pady=10, anchor=tk.W)

        func_frame = ttk.Frame(self.frame)
        ttk.Label(func_frame, text="主治：", font=("Microsoft YaHei UI", 12)).pack(side=tk.LEFT)
        self.func_value = ttk.Label(func_frame, text="心痛、心悸、胃痛、失眠", font=("Microsoft YaHei UI", 11), wraplength=250)
        self.func_value.pack(side=tk.LEFT)
        func_frame.pack(pady=10, anchor=tk.W)

        status_frame = ttk.LabelFrame(self.frame, text="检测状态", padding=10)
        self.status_label = ttk.Label(status_frame, text="等待算法输出", font=("Microsoft YaHei UI", 10), foreground="gray")
        self.status_label.pack()
        self.confidence_label = ttk.Label(status_frame, text="", font=("Microsoft YaHei UI", 10))
        self.confidence_label.pack()
        status_frame.pack(pady=30, fill=tk.X)

    def update_by_name(self, name: str, confidence: float = 0.0):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                info = db.get("内关", {})
                pos = info.get("position", "暂无数据")
                eff = info.get("effect", "暂无数据")
            except:
                pos = "数据库读取失败"
                eff = "数据库读取失败"
        else:
            pos = "未找到穴位数据库"
            eff = "请创建 acupoints_db.json"

        self.name_value.config(text=name)
        self.pos_value.config(text=pos)
        self.func_value.config(text=eff)
        self.status_label.config(text=f"当前穴位：{name}", foreground="green")
        if confidence > 0:
            self.confidence_label.config(text=f"置信度：{confidence:.2f}")
        else:
            self.confidence_label.config(text="")

    def update_both(self, left: dict, right: dict):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                info = db.get("内关", {})
                pos = info.get("position", "暂无数据")
                eff = info.get("effect", "暂无数据")
            except:
                pos = "数据库读取失败"
                eff = "数据库读取失败"
        else:
            pos = "未找到穴位数据库"
            eff = "请创建 acupoints_db.json"

        self.name_value.config(text="内关")
        self.coord_left.config(text=f"({left['x']}, {left['y']})  conf={left['confidence']}")
        self.coord_right.config(text=f"({right['x']}, {right['y']})  conf={right['confidence']}")
        self.pos_value.config(text=pos)
        self.func_value.config(text=eff)
        self.status_label.config(text="双侧检测中", foreground="green")
        self.confidence_label.config(text="")


class AcupointApp:
    def __init__(self, root):
        self.root = root
        self.root.title("穴位定位系统 - 内关穴智能定位")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        self._create_layout()
        self._init_components()

        self.root.bind("<<AcupointUpdated>>", self._on_acupoint_update)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_layout(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_area = ttk.Frame(main_container)
        left_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(left_area)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        self.start_btn = ttk.Button(btn_frame, text="启动摄像头", command=self._start_cam)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="停止摄像头", command=self._stop_cam)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.camera_frame = ttk.Frame(left_area, relief='sunken', borderwidth=2)
        self.camera_frame.pack(fill=tk.BOTH, expand=True)

        self.info_frame = ttk.Frame(main_container, relief='raised', borderwidth=2)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

    def _init_components(self):
        self.camera_panel = CameraPanel(self.camera_frame)
        self.camera_panel.frame.pack(fill=tk.BOTH, expand=True)

        self.info_panel = AcupointInfoPanel(self.info_frame)
        self.info_panel.frame.pack(fill=tk.Y, expand=True)

        try:
            self.camera_panel.start_camera()
        except RuntimeError as e:
            messagebox.showerror("错误", str(e))

    def _start_cam(self):
        if not self.camera_panel.is_running:
            try:
                self.camera_panel.start_camera()
            except RuntimeError as e:
                messagebox.showerror("错误", str(e))

    def _stop_cam(self):
        if self.camera_panel.is_running:
            self.camera_panel.stop_camera()

    def _on_acupoint_update(self, event):
        cam = self.camera_panel
        left = cam.acupoint_left
        right = cam.acupoint_right
        if left and right:
            self.info_panel.update_both(left, right)
        elif left:
            self.info_panel.update_by_name(left["name"], left["confidence"])
        elif right:
            self.info_panel.update_by_name(right["name"], right["confidence"])

    def _on_closing(self):
        cam = self.camera_panel
        if cam.esp32_ctrl:
            cam.esp32_ctrl.send_command(90, 90, 0)
            cam.esp32_ctrl.disconnect()
        cam.stop_camera()
        if cam.detector:
            cam.detector.release()
        self.root.destroy()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--esp32', action='store_true')
    parser.add_argument('--com', type=str, default=None)
    args = parser.parse_args()

    root = tk.Tk()
    app = AcupointApp(root)

    if args.esp32:
        from esp32.serial_controller import ESP32Controller
        ctrl = ESP32Controller(port=args.com)
        if ctrl.connect():
            app.camera_panel.set_esp32(ctrl)

    root.mainloop()


if __name__ == "__main__":
    main()
