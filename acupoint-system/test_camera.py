import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("摄像头打开失败！")
else:
    print("摄像头正常！")
    ret, frame = cap.read()
    if ret:
        print(f"画面尺寸: {frame.shape}")
    cap.release()