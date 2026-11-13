# Kiểm thử nghiệm thu thủ công

Các mục dưới đây chưa được chạy trong phiên phát triển tự động vì cần webcam, màn hình đồ họa và TurtleBot 4 Simulator đang hoạt động. Chỉ đổi trạng thái sau khi quan sát trực tiếp.

| Hạng mục | Trạng thái | Minh chứng/Ghi chú |
| --- | --- | --- |
| Webcam mở và overlay cập nhật thời gian thực | NOT RUN | Webcam/FER headless đã chạy sạch 12 giây; còn cần quan sát GUI |
| FER xử lý frame webcam thật mà không crash | PASS | Headless smoke test 12 giây, session `c8c5d1ad`, thoát sạch bằng SIGINT |
| Happy được nhận diện và chạy cong trái | NOT RUN | Cần simulator |
| Sad được nhận diện và chạy cong phải | NOT RUN | Cần simulator |
| Neutral dừng robot | NOT RUN | Cần simulator |
| Angry lùi 0,20 m | NOT RUN | Cần simulator |
| Surprise xoay đủ một vòng | NOT RUN | Cần simulator |
| Fear tiến 0,20 m | NOT RUN | Cần simulator |
| Mất khuôn mặt làm robot dừng | NOT RUN | Cần webcam + simulator |
| Đóng camera/Q làm robot dừng theo watchdog | NOT RUN | Cần webcam + simulator |
| Mất hoặc pause odometry làm robot dừng | NOT RUN | Cần simulator |
