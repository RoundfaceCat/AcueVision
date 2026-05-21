import cv2

print("正在启动简化版程序...")

# 打开摄像头
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ 摄像头打开失败！")
    exit()

print("✅ 摄像头打开成功！")
print("按 q 退出")

while True:
    ret, frame = cap.read()
    if not ret:
        print("读取画面失败")
        break
    
    # 在画面中心画一个红点（测试用）
    h, w = frame.shape[:2]
    cv2.circle(frame, (w//2, h//2), 20, (0, 0, 255), -1)
    cv2.putText(frame, "Camera Working!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 显示画面
    cv2.imshow("Camera Test", frame)
    
    # 按q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("程序已退出")