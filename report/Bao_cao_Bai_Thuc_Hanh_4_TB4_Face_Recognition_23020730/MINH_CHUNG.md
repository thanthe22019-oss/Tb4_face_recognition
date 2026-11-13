# Liên kết minh chứng

Báo cáo không lưu hoặc yêu cầu chụp các file ảnh theo tên cố định. Người thực
hiện có thể gửi một URL album/thư mục chứa ảnh minh chứng; URL đó được đặt tại
`evidence-link.tex` và xuất hiện một lần trong Chương 6.

Bộ minh chứng nên cho phép đối chiếu các nội dung sau:

- overlay có box, nhãn, confidence và trạng thái;
- sáu biểu cảm `happy`, `sad`, `neutral`, `angry`, `surprise`, `fear`;
- preview với vận tốc bằng zero;
- năm quỹ đạo chuyển động và trạng thái hoàn tất;
- neutral/no-face và watchdog odometry đưa vận tốc về zero;
- kết quả `ros2 topic info /cmd_vel -v` nếu nghiệm thu publisher duy nhất.

Không cần đúng số lượng hoặc tên ảnh. Chỉ chuyển một hàng PENDING trong báo cáo
thành PASS khi nội dung tại URL thể hiện đủ điều kiện của hàng đó.
