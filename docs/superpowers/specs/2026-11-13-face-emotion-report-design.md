# Thiết kế báo cáo nhận diện biểu cảm và điều khiển TurtleBot 4

## Mục đích

Tạo một báo cáo LaTeX tiếng Việt theo mẫu UET/TurtleBot 4 đã dùng ở các bài
trước, trình bày đầy đủ thiết kế, mã nguồn, quy trình chạy, kiểm thử và kết quả
của package `tbe4_face_recognition`. Báo cáo phục vụ giảng viên và trợ giảng,
đồng thời phải có thể cập nhật bằng một URL khi người dùng cung cấp bộ ảnh
nghiệm thu webcam và simulator.

## Đầu ra và người đọc

- Người đọc: giảng viên và trợ giảng môn học.
- Tác giả: Thân Thế Trí Dũng, MSSV 23020730, lớp QH-2023-I/CQ-E-RE.
- Thư mục đầu ra:
  `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/`.
- Sản phẩm: source LaTeX nhiều file, tài liệu hướng dẫn liên kết minh chứng,
  tài liệu tham khảo và PDF đã biên dịch.

## Mẫu tham khảo

Giữ bố cục, trang bìa, font tiếng Việt, bảng, code block, màu sắc và logo từ:

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
  trường ảo vào repository; chỉ dẫn tới bộ ảnh do người dùng cung cấp.

## Hình minh họa

- Dùng TikZ hoặc Mermaid chuyển thành hình cho sơ đồ kiến trúc và state machine.
- Không tạo placeholder ảnh hoặc yêu cầu tên file ảnh cố định.
- Khai báo một liên kết trong `evidence-link.tex`; Chương 6 nêu tiêu chí cần
  đối chiếu tại liên kết trước khi chuyển từng hàng từ PENDING sang PASS.

## Các phương án

### LaTeX nhiều file theo mẫu UET — chọn

Phù hợp với các báo cáo trước, dễ biên dịch PDF và cho phép cập nhật liên kết
minh chứng mà không đưa ảnh khuôn mặt vào repository.

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
- PDF không phụ thuộc file ảnh nghiệm thu; URL minh chứng có thể bổ sung sau.
- Không sửa mã ROS 2, cấu hình vận hành hoặc test của ứng dụng khi viết báo cáo.
