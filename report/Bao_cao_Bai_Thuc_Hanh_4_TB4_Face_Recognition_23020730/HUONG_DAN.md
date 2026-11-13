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

## Bổ sung liên kết minh chứng

Báo cáo không yêu cầu lưu ảnh vào repository. Khi có URL album hoặc thư mục
ảnh minh chứng, sửa một dòng trong `evidence-link.tex` theo mẫu:

```tex
\newcommand{\evidenceLink}{\href{https://example.com}{Mở bộ ảnh minh chứng}}
```

Sau khi đối chiếu nội dung liên kết, cập nhật riêng các trạng thái PENDING ở
Chương 6. Một URL tồn tại chưa đủ để tự động coi mọi ca là PASS.

## Biên dịch LaTeX

Trên Ubuntu có TeX Live:

```bash
cd ~/Interaction/tbe4_face_recognition/report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

Nếu thiếu công cụ:

```bash
sudo apt update
sudo apt install texlive-xetex texlive-latex-extra texlive-lang-other texlive-fonts-recommended
```

Có thể dùng Tectonic portable thay cho TeX Live:

```bash
tectonic -X compile main.tex
```

## Kiểm tra trước khi nộp

- Đọc bảng PENDING trong chương 6 và chỉ thay bằng kết quả đã đối chiếu.
- Kiểm tra quyền truy cập của URL minh chứng, không commit frame hoặc crop mặt.
- Kiểm tra repository URL và bổ sung video URL nếu đã public.
- Chạy `pdfinfo main.pdf` để kiểm tra số trang và metadata file.
