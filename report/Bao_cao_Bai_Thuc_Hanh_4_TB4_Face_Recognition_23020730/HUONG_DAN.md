# Hướng dẫn sử dụng và biên dịch báo cáo

## Chạy lại dự án

```bash
cd ~/Interaction/tbe4_face_recognition
./scripts/setup_face_venv.sh
./scripts/build.sh
./scripts/run_recognition.sh
```

Sau khi preview và simulator đã sẵn sàng:

```bash
./scripts/run_interaction.sh preview_only:=false
```

Một khuôn mặt duy nhất có confidence lớn hơn `0.60` được xử lý ngay. Controller
vẫn giữ one-shot, neutral re-arm tức thời, unknown/no-face re-arm sau 0,75 giây
và các watchdog observation/odometry.

## Biên dịch LaTeX

Trên Ubuntu có TeX Live:

```bash
cd ~/Interaction/tbe4_face_recognition/report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Nếu thiếu công cụ:

```bash
sudo apt update
sudo apt install texlive-latex-extra texlive-lang-other texlive-fonts-recommended
```

Ảnh chưa có sẽ hiện thành placeholder và không làm LaTeX dừng. Sau khi thêm
ảnh đúng tên vào `images/`, chạy lại chuỗi lệnh trên để tạo PDF mới.

## Kiểm tra trước khi nộp

- Đọc bảng PENDING trong chương 6 và thay bằng kết quả thật sau khi thử.
- Chỉ thêm ảnh do người thực hiện chọn; không lưu video thô hoặc crop khuôn mặt.
- Kiểm tra repository URL và bổ sung video URL nếu đã public.
- Chạy `pdfinfo main.pdf` để kiểm tra số trang và metadata file.
