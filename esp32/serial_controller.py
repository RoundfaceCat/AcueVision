"""
串口通信模块 - 向 ESP32 发送舵机角度和激光控制指令

指令格式: 水平角度,垂直角度,激光开关
示例: 90,45,1
"""

import serial
import serial.tools.list_ports
from typing import Optional


class ESP32Controller:
    """ESP32 串口控制器"""

    def __init__(self, port: Optional[str] = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None

    @staticmethod
    def list_ports():
        """列出可用串口"""
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]

    @staticmethod
    def auto_detect():
        """自动检测 ESP32 串口 (Windows)"""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if "CH340" in p.description or "CP210" in p.description or "ESP32" in p.description:
                return p.device
        return None

    def connect(self, port: Optional[str] = None) -> bool:
        """连接串口"""
        target = port or self.port or self.auto_detect()
        if not target:
            print("[ESP32] 未找到可用串口")
            return False
        try:
            self.ser = serial.Serial(target, self.baudrate, timeout=1)
            print(f"[ESP32] 已连接: {target}")
            return True
        except Exception as e:
            print(f"[ESP32] 连接失败: {e}")
            return False

    def send_command(self, angle_h: int, angle_v: int, laser: int) -> bool:
        """发送控制指令"""
        if self.ser is None or not self.ser.is_open:
            return False
        try:
            cmd = f"{angle_h},{angle_v},{laser}\n"
            self.ser.write(cmd.encode())
            return True
        except Exception as e:
            print(f"[ESP32] 发送失败: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[ESP32] 已断开")

    def __del__(self):
        self.disconnect()
