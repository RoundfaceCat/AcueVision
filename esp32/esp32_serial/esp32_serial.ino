/*
 * 穴位定位系统 - ESP32 硬件控制端
 *
 * 接收上位机串口指令, 控制两轴舵机 + 激光
 *
 * 指令格式: 水平角度,垂直角度,激光开关
 * 示例: 90,45,1
 *   水平角度: 0-180 (舵机1, 左右)
 *   垂直角度: 0-180 (舵机2, 上下)
 *   激光开关: 0=关,  1=开
 *
 * 接线:
 *   舵机1 (水平): GPIO 12
 *   舵机2 (垂直): GPIO 13
 *   激光模块:     GPIO 14
 *   串口:         USB 默认 Serial
 */

#include <Arduino.h>
#include <ESP32Servo.h>

// ==== 引脚定义 ====
#define SERVO_H_PIN  12    // 水平舵机
#define SERVO_V_PIN  13    // 垂直舵机
#define LASER_PIN    14    // 激光模块

// ==== 舵机实例 ====
Servo servoH;
Servo servoV;

// ==== 当前状态 ====
int curAngleH = 90;
int curAngleV = 90;
bool laserOn = false;

// ==== 串口缓冲区 ====
String inputBuffer = "";

// ==== 函数原型 ====
void parseCommand(String cmd);
void moveServo(Servo &servo, int &current, int target);

void setup() {
  Serial.begin(115200);

  servoH.attach(SERVO_H_PIN);
  servoV.attach(SERVO_V_PIN);

  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);

  servoH.write(90);
  servoV.write(90);

  Serial.println("ESP32 Acupoint Laser System Ready");
  Serial.println("Format: 水平角度,垂直角度,激光开关");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        parseCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }
}

void parseCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  int comma1 = cmd.indexOf(',');
  int comma2 = cmd.indexOf(',', comma1 + 1);

  if (comma1 == -1 || comma2 == -1) {
    Serial.println("ERROR: Invalid format. Use: angleH,angleV,laserState");
    return;
  }

  int angleH = cmd.substring(0, comma1).toInt();
  int angleV = cmd.substring(comma1 + 1, comma2).toInt();
  int laserState = cmd.substring(comma2 + 1).toInt();

  if (angleH < 0) angleH = 0;
  if (angleH > 180) angleH = 180;
  if (angleV < 0) angleV = 0;
  if (angleV > 180) angleV = 180;

  moveServo(servoH, curAngleH, angleH);
  moveServo(servoV, curAngleV, angleV);

  digitalWrite(LASER_PIN, (laserState == 1) ? HIGH : LOW);
  laserOn = (laserState == 1);

  Serial.printf("OK: H=%d V=%d L=%d\n", angleH, angleV, laserState);
}

void moveServo(Servo &servo, int &current, int target) {
  if (target == current) return;

  int step = (target > current) ? 1 : -1;
  for (int pos = current; pos != target; pos += step) {
    servo.write(pos);
    delay(10);
  }
  servo.write(target);
  current = target;
}
