# Thiết kế báo cáo nhận diện biểu cảm và điều khiển TurtleBot 4

## Mục đích

Tạo một báo cáo LaTeX tiếng Việt theo mẫu UET/TurtleBot 4 đã dùng ở các bài
trước, trình bày đầy đủ thiết kế, mã nguồn, quy trình chạy, kiểm thử và kết quả
của package `tbe4_face_recognition`. Báo cáo phục vụ giảng viên và trợ giảng,
đồng thời phải có thể cập nhật tự động khi người dùng bổ sung ảnh nghiệm thu
webcam và simulator.

## Đầu ra và người đọc

- Người đọc: giảng viên và trợ giảng môn học.
- Tác giả: Thân Thế Trí Dũng, MSSV 23020730, lớp QH-2023-I/CQ-E-RE.
- Thư mục đầu ra:
  `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/`.
- Sản phẩm: source LaTeX nhiều file, tài liệu hướng dẫn, danh sách ảnh cần chụp,
  tài liệu tham khảo và PDF được biên dịch khi máy có đủ TeX Live.

## Mẫu tham khảo

Giữ bố cục, trang bìa, font tiếng Việt, bảng, code block, màu sắc, logo và cơ
chế placeholder ảnh từ:

`/home/alex/Interaction/tb4_nav2/report/Bao_cao_TurtleBot4_SLAM_Nav2_23020730/`

Thư mục tham khảo chỉ được đọc. Chỉ sao chép tài nguyên dùng chung; toàn bộ nội
dung kỹ thuật phải được viết lại cho bài nhận diện biểu cảm.

## Cấu trúc nội dung

1. Trang bìa, mục tiêu và yêu cầu bài thực hành.
2. Kiến trúc hai node ROS 2, topic JSON, `/odom` và `/cmd_vel`.
3. Nhận diện khuôn mặt qua webcam bằng OpenCV và FER/TFLite.
4. Chuẩn hóa observation, ngưỡng confidence lớn hơn 60%, xử lý tức thời và watchdog.
5. State machine one-shot, preview mặc định và điều kiện re-arm.
6. Năm profile chuyển động dùng odometry và hành vi dừng của `neutral`.
7. Cấu trúc package, launch, YAML, virtualenv và quy trình chạy simulator.
8. Kiểm thử tự động và bảng nghiệm thu thủ công.
9. Kết luận, giới hạn, hướng phát triển và tài liệu tham khảo.

## Bằng chứng được phép sử dụng

- Có thể ghi nhận: commit `c35bdd5`, 102 pytest pass, colcon build thành công,
  colcon test có 102 test, 0 lỗi, 0 thất bại, 0 bỏ qua; package prefix và ba
  launch description đã được ROS 2 nạp bằng `--show-args`.
- Các kết quả trên đã được xác minh trực tiếp tại commit ứng dụng `c35bdd5`.
- Không được tuyên bố FER đã nhận đúng sáu biểu cảm, webcam đã chạy ổn định,
  robot đã hoàn thành quỹ đạo hoặc các cơ chế dừng đã qua nghiệm thu simulator
  khi chưa có ảnh/video/log thật.
- Mọi kết quả chưa chạy dùng macro `\pending` và nêu đúng thao tác cần thực hiện.
- Không đưa frame webcam, crop khuôn mặt, video, dữ liệu sinh trắc hoặc file môi
  trường ảo vào repository nếu người dùng chưa chủ động chọn ảnh minh chứng.

## Hình minh họa

- Dùng TikZ hoặc Mermaid chuyển thành hình cho sơ đồ kiến trúc và state machine.
- Tạo placeholder có tên cụ thể cho overlay webcam, topic observation/status,
  preview zero velocity, năm chuyển động non-neutral, neutral/no-face stop,
  odometry timeout và kết quả test.
- `HUONG_DAN_CHUP_ANH.md` phải mô tả nội dung bắt buộc của từng ảnh và tránh lộ
  khuôn mặt ngoài người thực hiện.

## Các phương án

### LaTeX nhiều file theo mẫu UET — chọn

Phù hợp với các báo cáo trước, dễ biên dịch PDF, tái sử dụng macro placeholder
và cho phép cập nhật từng chương hoặc từng ảnh độc lập.

### Báo cáo Markdown rồi chuyển PDF

Nhanh hơn nhưng khó giữ đúng trang bìa, font, bảng dài và bố cục quen thuộc của
các bài trước.

### Báo cáo ngắn một file

Ít file hơn nhưng không đủ chỗ giải thích pipeline AI, cơ chế an toàn, sáu ánh
xạ hành động và bằng chứng nghiệm thu.

## Tiêu chí hoàn thành

- Source LaTeX có cấu trúc đầy đủ và biên dịch không có lỗi nghiêm trọng khi
  toolchain sẵn sàng.
- Nội dung kỹ thuật khớp source, YAML, README và test của commit được ghi nhận.
- Kết quả tự động và kết quả thủ công được phân biệt rõ.
- Ảnh chưa có vẫn tạo placeholder biên dịch được và có hướng dẫn thay thế.
- Không sửa mã ROS 2, cấu hình vận hành hoặc test của ứng dụng khi viết báo cáo.
