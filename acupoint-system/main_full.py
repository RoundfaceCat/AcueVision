import cv2
import math
import json

print("=" * 50)
print("   内关穴定位系统 - 视觉模块 (兼容版)")
print("=" * 50)

# 打开摄像头
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ 摄像头打开失败！")
    exit()

print("✅ 摄像头打开成功！")
print("说明：本版本使用人体检测模拟关键点")
print("按 'q' 退出")
print("-" * 50)

# 初始化人体检测器
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("读取画面失败")
        break
    
    frame_count += 1
    h, w = frame.shape[:2]
    
    # 缩小图片加快检测速度
    small_frame = cv2.resize(frame, (w//2, h//2))
    boxes, weights = hog.detectMultiScale(small_frame, winStride=(4, 4))
    
    # 模拟关键点数据
    keypoints = {
        "left_wrist": None,
        "left_elbow": None,
        "left_shoulder": None
    }
    
    if len(boxes) > 0:
        # 取第一个检测到的人
        x, y, bw, bh = boxes[0]
        # 坐标还原回原图大小
        x *= 2
        y *= 2
        bw *= 2
        bh *= 2
        
        # 绘制人体框
        cv2.rectangle(frame, (x, y), (x+bw, y+bh), (0, 255, 0), 2)
        
        # 根据人体框估算关键点位置
        # 肩膀：框的上方 1/4 处
        shoulder_x = x + bw // 2
        shoulder_y = y + int(bh * 0.2)
        
        # 手肘：框的中部
        elbow_x = x + bw // 2
        elbow_y = y + int(bh * 0.5)
        
        # 手腕：框的底部
        wrist_x = x + bw // 2
        wrist_y = y + bh - 20
        
        # 转换为普通 int（解决 JSON 序列化问题）
        shoulder_x = int(shoulder_x)
        shoulder_y = int(shoulder_y)
        elbow_x = int(elbow_x)
        elbow_y = int(elbow_y)
        wrist_x = int(wrist_x)
        wrist_y = int(wrist_y)
        
        keypoints["left_shoulder"] = [shoulder_x, shoulder_y]
        keypoints["left_elbow"] = [elbow_x, elbow_y]
        keypoints["left_wrist"] = [wrist_x, wrist_y]
        
        # 计算内关穴位置（腕上2寸，按比例约手腕到肘的 1/6）
        # 内关 = 手腕 + (手肘 - 手腕) × (2/12)
        neiguan_x = wrist_x + (elbow_x - wrist_x) * 2 // 12
        neiguan_y = wrist_y + (elbow_y - wrist_y) * 2 // 12
        neiguan_x = int(neiguan_x)
        neiguan_y = int(neiguan_y)
        
        # 画关键点
        cv2.circle(frame, (wrist_x, wrist_y), 10, (0, 0, 255), -1)  # 手腕：红点
        cv2.circle(frame, (elbow_x, elbow_y), 10, (0, 255, 0), -1)   # 手肘：绿点
        cv2.circle(frame, (shoulder_x, shoulder_y), 10, (255, 0, 0), -1)  # 肩膀：蓝点
        cv2.circle(frame, (neiguan_x, neiguan_y), 12, (0, 255, 255), -1)  # 内关：黄点
        
        # 标注文字
        cv2.putText(frame, "Wrist", (wrist_x+10, wrist_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, "Elbow", (elbow_x+10, elbow_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, "Neiguan", (neiguan_x+10, neiguan_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # 画出连接线（手腕到手肘，手肘到肩膀）
        cv2.line(frame, (wrist_x, wrist_y), (elbow_x, elbow_y), (255, 255, 255), 2)
        cv2.line(frame, (elbow_x, elbow_y), (shoulder_x, shoulder_y), (255, 255, 255), 2)
        
        # 输出 JSON 格式（这是给其他模块的接口）
        output_data = {
            "left_wrist": [wrist_x, wrist_y],
            "left_elbow": [elbow_x, elbow_y],
            "left_shoulder": [shoulder_x, shoulder_y],
            "neiguan": [neiguan_x, neiguan_y],
            "timestamp": frame_count
        }
        
        # 每30帧输出一次，避免刷屏
        if frame_count % 30 == 0:
            print(f"[JSON] {json.dumps(output_data)}")
    
    # 显示信息
    cv2.putText(frame, "Neiguan (Inner Gate) Localization", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Press 'q' to quit", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    if len(boxes) == 0:
        cv2.putText(frame, "No person detected", (w//2-100, h//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # 显示画面
    cv2.imshow("Acupoint Localization System", frame)
    
    # 按q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\n程序已退出")
print("=" * 50)