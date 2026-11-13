# Hướng dẫn chụp ảnh minh chứng

Lưu ảnh trong thư mục `images/` với đúng tên dưới đây. Ảnh camera phải do người
thực hiện chủ động chọn, tránh người ngoài khung hình và không lưu chuỗi frame
hoặc video thô vào Git.

| File | Nội dung bắt buộc |
| --- | --- |
| `01_kien_truc_he_thong.png` | Node/topic graph hoặc sơ đồ kiến trúc hai node và `/cmd_vel`. |
| `02_overlay_nhan_dien.png` | Một khuôn mặt, box, nhãn FER, confidence >0,60 và status robot. |
| `03_sau_bieu_cam.png` | Sáu biểu cảm happy, sad, neutral, angry, surprise, fear; có thể ghép sáu ảnh. |
| `04_topics_observation_status.png` | JSON hợp lệ trên `/emotion_observation` và `/emotion_behavior_status`. |
| `05_preview_zero_cmd_vel.png` | Status `preview_completed` và Twist bằng zero. |
| `06_happy_cong_trai.png` | Robot/simulator thực hiện cung trái, kèm action/status. |
| `07_sad_cong_phai.png` | Robot/simulator thực hiện cung phải, kèm action/status. |
| `08_angry_lui.png` | Robot lùi và dừng sau khoảng 0,20 m. |
| `09_surprise_xoay_360.png` | Tiến độ xoay và trạng thái completed sau một vòng. |
| `10_fear_tien.png` | Robot tiến và dừng sau khoảng 0,20 m. |
| `11_neutral_no_face_stop.png` | Neutral hoặc mất mặt khi đang chạy làm `/cmd_vel` về zero. |
| `12_odom_watchdog.png` | Mất/pause odometry làm status báo dừng và Twist bằng zero. |
| `13_kiem_thu_tu_dong.png` | Dòng tổng kết pytest và `colcon test-result --verbose`. |

## Trình tự gợi ý

1. Chạy recognition riêng để chụp ảnh 02--03.
2. Chạy interaction ở preview để chụp ảnh 04--05.
3. Mở simulator, undock, bảo đảm vùng trống rồi bật motion.
4. Thử từng biểu cảm, luôn đưa về Neutral giữa hai action.
5. Chụp topic/status đồng thời với simulator để ảnh thể hiện cả lệnh và kết quả.
6. Thử các tình huống dừng cuối cùng; không tắt odometry khi robot ở gần vật cản.

Không đổi trạng thái PENDING thành PASS chỉ dựa trên một frame không thể hiện
đầy đủ hành động. Với chuyển động, video ngắn hoặc nhiều ảnh có timestamp sẽ có
giá trị đối chiếu tốt hơn một ảnh tĩnh.
