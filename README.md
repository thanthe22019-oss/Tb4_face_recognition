# TurtleBot 4 — Nhận diện biểu cảm khuôn mặt

Package ROS 2 Humble nhận diện biểu cảm từ webcam laptop bằng FER/TFLite và điều khiển TurtleBot 4 qua `/cmd_vel`. Hai node độc lập giao tiếp bằng `/emotion_observation`: node AI không giữ vòng điều khiển robot, còn controller không import TensorFlow.

## Yêu cầu

- Ubuntu 22.04, Python 3.10, ROS 2 Humble.
- TurtleBot 4 Simulator/Ignition Fortress hoặc TurtleBot 4 thật đã cấu hình ROS 2.
- Webcam laptop, mặc định `/dev/video0`.
- Khu vực thử nghiệm trống; bài này không chạy Nav2 hay tránh vật cản.

## Cài môi trường và build

Không cài FER/TensorFlow vào Python hệ thống của ROS. Script dưới đây tạo `.venv-face`, giữ quyền truy cập `rclpy` hệ thống và cài dependency AI đã pin:

```bash
cd ~/Interaction/tbe4_face_recognition
./scripts/setup_face_venv.sh
./scripts/build.sh
```

## Kiểm tra webcam trước

```bash
cd ~/Interaction/tbe4_face_recognition
./scripts/run_recognition.sh
```

Cửa sổ hiển thị khung mặt, nhãn FER, confidence và số khuôn mặt. Nhấn `Q` hoặc `Ctrl+C` để đóng. Chọn camera khác bằng `camera_index:=1`; chạy không có cửa sổ bằng `show_window:=false`.

## Chạy TurtleBot 4 Simulator

Terminal 1:

```bash
cd ~/Interaction/tbe4_face_recognition
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch tbe4_face_recognition simulation.launch.py
```

Launch này chỉ mở simulator, không mở Nav2, SLAM hoặc localization. Chờ robot và controller mô phỏng sẵn sàng, sau đó undock trong terminal 2:

```bash
source /opt/ros/humble/setup.bash
source ~/Interaction/tbe4_face_recognition/install/setup.bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}' --feedback
```

Chờ action báo `SUCCEEDED`, bảo đảm robot ở vùng trống và không chạy teleop/Nav2.

## Chạy tương tác

Lần đầu luôn chạy preview; controller vẫn lọc biểu cảm và publish status nhưng chỉ phát vận tốc zero:

```bash
cd ~/Interaction/tbe4_face_recognition
./scripts/run_interaction.sh
```

Quan sát `/emotion_behavior_status` có `odometry_ready: true`. Sau khi preview đúng, dừng phiên và bật chuyển động rõ ràng:

```bash
./scripts/run_interaction.sh preview_only:=false
```

Chỉ chạy một publisher điều khiển robot. Không mở teleop, Nav2 hoặc một phiên interaction thứ hai cùng lúc.

## Ánh xạ biểu cảm

Biểu cảm phải ổn định 0,5 giây. Một hành động chỉ chạy một lần; cần giữ Neutral hoặc mất mặt đủ 0,75 giây để re-arm.

| Biểu cảm | Hành động mặc định |
| --- | --- |
| Happy | Cong trái, bán kính 0,40 m, đổi hướng 60° |
| Sad | Cong phải, bán kính 0,40 m, đổi hướng 60° |
| Neutral | Dừng và re-arm |
| Angry | Lùi 0,20 m, tối đa 0,08 m/s |
| Surprise | Xoay trái đủ 360°, tối đa 0,40 rad/s |
| Fear | Tiến 0,20 m, tối đa 0,10 m/s |

`disgust`, confidence dưới 0,55, không có mặt hoặc nhiều mặt đều dừng/không kích hoạt. Observation quá 0,75 giây hoặc odometry quá 0,5 giây cũng đưa `/cmd_vel` về zero. Thông số nằm trong `config/controller.yaml` và `config/recognition.yaml`.

## Quan sát topic

Mỗi lệnh chạy trong một terminal đã source ROS và `install/setup.bash`:

```bash
ros2 topic echo /emotion_observation
ros2 topic echo /emotion_behavior_status
ros2 topic echo /cmd_vel
ros2 topic hz /odom
```

`/emotion_observation` và `/emotion_behavior_status` là JSON trong `std_msgs/String`. Controller là node duy nhất của dự án publish `/cmd_vel`.

## Kiểm thử tự động

```bash
cd ~/Interaction/tbe4_face_recognition
source /opt/ros/humble/setup.bash
pytest -q
colcon build --base-paths . --packages-select tbe4_face_recognition --symlink-install
colcon test --base-paths . --packages-select tbe4_face_recognition
colcon test-result --verbose
```

Kiểm thử webcam và simulator được ghi riêng trong `docs/acceptance.md`; trạng thái `NOT RUN` không được hiểu là đã đạt.

## Xử lý lỗi thường gặp

- `Cannot open /dev/videoN`: đóng ứng dụng đang giữ webcam hoặc truyền đúng `camera_index`.
- Thiếu `fer`/TensorFlow: chạy lại `./scripts/setup_face_venv.sh`, không dùng `sudo pip`.
- `odometry_ready=false`: kiểm tra `/odom`, simulator/robot và domain DDS trước khi bật motion.
- Robot không chạy trong preview: đây là hành vi đúng; dùng `preview_only:=false` sau khi đã kiểm tra.
- Robot nhận nhiều nguồn lệnh: dừng teleop/Nav2/interaction cũ rồi chỉ mở một phiên.
- Nhận diện dao động: giữ một khuôn mặt đủ sáng, nhìn thẳng webcam và chờ qua ngưỡng ổn định.

Thiết kế và implementation plan nằm trong `docs/superpowers/`.
