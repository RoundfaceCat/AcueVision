"""
穴位定位界面 - 完整版（满足软件成员B所有任务）
- 摄像头显示 + 手动启停按钮
- 红点根据 output.json 移动
- 右侧穴位信息动态从 acupoints_db.json 读取
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import json
import os


class CameraPanel:
    """摄像头面板 - 显示摄像头 + 画红点"""

    def __init__(self, parent, width=640, height=480):
        self.parent = parent
        self.width = width
        self.height = height

        self.frame = ttk.Frame(parent)
        self.camera_label = ttk.Label(self.frame)
        self.camera_label.pack(fill=tk.BOTH, expand=True)

        self.cap = None
        self.is_running = False
        self.acupoint_x = width // 2
        self.acupoint_y = height // 2

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

    def update_acupoint_position(self, x: int, y: int):
        self.acupoint_x = x
        self.acupoint_y = y

    def _update_frame(self):
        if self.is_running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                # 画红点
                cv2.circle(frame, (self.acupoint_x, self.acupoint_y), 8, (0, 0, 255), -1)
                # 显示
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(img)
                self.camera_label.configure(image=img_tk)
                self.camera_label.image = img_tk
        if self.is_running:
            self.parent.after(30, self._update_frame)


class AcupointInfoPanel:
    """穴位信息面板 - 动态显示"""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=20)
        self.db_path = os.path.join(os.path.dirname(__file__), "acupoints_db.json")

        # 标题
        ttk.Label(self.frame, text="穴位定位", font=("Microsoft YaHei UI", 16, "bold")).pack(pady=(0, 20))
        ttk.Separator(self.frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # 穴位名称行
        name_frame = ttk.Frame(self.frame)
        ttk.Label(name_frame, text="穴位名称：", font=("Microsoft YaHei UI", 12)).pack(side=tk.LEFT)
        self.name_value = ttk.Label(name_frame, text="内关", font=("Microsoft YaHei UI", 12, "bold"), foreground="#d32f2f")
        self.name_value.pack(side=tk.LEFT)
        name_frame.pack(pady=15, anchor=tk.W)

        # 位置行
        pos_frame = ttk.Frame(self.frame)
        ttk.Label(pos_frame, text="位置：", font=("Microsoft YaHei UI", 12)).pack(side=tk.LEFT)
        self.pos_value = ttk.Label(pos_frame, text="前臂掌侧，腕横纹上 2 寸", font=("Microsoft YaHei UI", 11))
        self.pos_value.pack(side=tk.LEFT)
        pos_frame.pack(pady=10, anchor=tk.W)

        # 主治行
        func_frame = ttk.Frame(self.frame)
        ttk.Label(func_frame, text="主治：", font=("Microsoft YaHei UI", 12)).pack(side=tk.LEFT)
        self.func_value = ttk.Label(func_frame, text="心痛、心悸、胃痛、失眠", font=("Microsoft YaHei UI", 11), wraplength=250)
        self.func_value.pack(side=tk.LEFT)
        func_frame.pack(pady=10, anchor=tk.W)

        # 状态显示
        status_frame = ttk.LabelFrame(self.frame, text="检测状态", padding=10)
        self.status_label = ttk.Label(status_frame, text="等待算法输出", font=("Microsoft YaHei UI", 10), foreground="gray")
        self.status_label.pack()
        status_frame.pack(pady=30, fill=tk.X)

    def update_by_name(self, name: str):
        """根据穴位名称更新右侧信息"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                info = db.get(name, {})
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


class AcupointApp:
    """主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("穴位定位系统 - 内关穴智能定位")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # 算法输出文件路径（统一使用 output.json）
        self.output_file = os.path.join(os.path.dirname(__file__), "output.json")
        self.monitor_id = None

        self._create_layout()
        self._init_components()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.start_monitoring()

    def _create_layout(self):
        """创建界面布局：左侧摄像头+按钮，右侧信息"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧区域（摄像头 + 按钮）
        left_area = ttk.Frame(main_container)
        left_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 按钮行（放在左侧顶部）
        btn_frame = ttk.Frame(left_area)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        self.start_btn = ttk.Button(btn_frame, text="启动摄像头", command=self._start_cam)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="停止摄像头", command=self._stop_cam)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 摄像头画面容器
        self.camera_frame = ttk.Frame(left_area, relief='sunken', borderwidth=2)
        self.camera_frame.pack(fill=tk.BOTH, expand=True)

        # 右侧信息面板
        self.info_frame = ttk.Frame(main_container, relief='raised', borderwidth=2)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

    def _init_components(self):
        self.camera_panel = CameraPanel(self.camera_frame)
        self.camera_panel.frame.pack(fill=tk.BOTH, expand=True)

        self.info_panel = AcupointInfoPanel(self.info_frame)
        self.info_panel.frame.pack(fill=tk.Y, expand=True)

        # 自动启动摄像头
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

    def start_monitoring(self):
        self.monitor_output()

    def monitor_output(self):
        print("UI 监控文件:", self.output_file)
        print("Checking file:", self.output_file)
        if os.path.exists(self.output_file):
            print("File exists")  
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print("Read data:", data)
                    name = data.get("name", "内关")
                    x = data.get("x", self.camera_panel.width // 2)
                    y = data.get("y", self.camera_panel.height // 2)
                    print(f"Updating to x={x}, y={y}")   
                    self.camera_panel.update_acupoint_position(x, y)
                    self.info_panel.update_by_name(name)
            except Exception as e:
                print("Error:", e)   # 添加
        else:
            print("File not found")
        self.monitor_id = self.root.after(100, self.monitor_output)
    def _on_closing(self):
        if self.monitor_id:
            self.root.after_cancel(self.monitor_id)
        self.camera_panel.stop_camera()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AcupointApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()