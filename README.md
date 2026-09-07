# TikDow

Ứng dụng desktop Python: dán link TikTok, chọn **MP4 video** hoặc **MP3 âm thanh**, chọn thư mục và tải xuống.

## Chạy trên Windows

1. Cài **Python 3.10+** (khuyến nghị 3.12), có **pip và Tcl/Tk**, chọn Add Python to PATH.
2. Cài **FFmpeg**, gồm cả `ffmpeg.exe` và `ffprobe.exe`. Thêm thư mục `bin` vào PATH hoặc chọn thư mục đó ngay trong TikDow. Xem [trang tải FFmpeg](https://ffmpeg.org/download.html).
3. Clone repo hoặc tải ZIP rồi giải nén vào thư mục có quyền ghi.
4. Nhấp đúp **`Start-TikDow.bat`**.

Lần đầu launcher tự tạo `.venv`, cài `requirements.txt`, rồi mở cửa sổ riêng. Cần Internet khi cài thư viện. Những lần sau dùng lại môi trường; chỉ cài lại khi requirements thay đổi hoặc kiểm tra import thất bại. Không cài thư viện vào Python hệ thống.

Có thể chạy bằng terminal:

```powershell
python launch.py
```

Ứng dụng từ chối chạy ngoài **`.venv` của chính repo**, kể cả một virtualenv khác. Không cần tự activate. Nếu Python đã thay phiên bản hoặc chuyển repo từ máy khác, xóa `.venv` rồi chạy launcher để tạo lại.

Linux/macOS: `python3 launch.py`. Cần Python có Tkinter, venv và FFmpeg; trên Ubuntu/Debian có thể cài `python3-tk python3-venv ffmpeg`. Windows là nền tảng mục tiêu chính.

## Sử dụng

- Dán link video TikTok đầy đủ hoặc link rút gọn `vt.tiktok.com` / `vm.tiktok.com`.
- Chọn MP4 hoặc MP3 (128/192/256/320 kbps).
- Chọn thư mục lưu, bấm **Tải xuống**. Có tiến trình, nhật ký, hủy tải và mở thư mục.
- Tải chạy ở tiến trình nền; nút Hủy dừng cả tiến trình tải/chuyển đổi. Chờ hủy hoàn tất trước khi đóng ứng dụng.
- MP4 ưu tiên luồng MP4, ghép/chuyển đổi bằng FFmpeg nếu cần; MP3 được trích xuất/chuyển mã thực sự, không chỉ đổi đuôi. Chất lượng phụ thuộc nguồn, chọn 320 kbps không phục hồi chi tiết đã mất.

## Settings JSON

Tự lưu tại **`settings/settings.json`** khi đổi lựa chọn, rời ô nhập, bắt đầu tải hoặc đóng ứng dụng:

- `format`: mp3/mp4.
- `output_dir`: thư mục đích; mặc định `~/Downloads/TikDow`.
- `mp3_bitrate`: bitrate MP3.
- `ffmpeg_dir`: thư mục chứa FFmpeg và FFprobe, trống để tìm trong PATH.

Ghi qua file tạm rồi thay thế nguyên tử. File thiếu/hỏng hoặc trường sai kiểu sẽ dùng mặc định. File settings cá nhân không đưa lên Git. Có mẫu `settings/settings.example.json`. Không lưu link đã dán.

## Phát triển và kiểm tra

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q tikdow launch.py
```

Cập nhật bộ trích xuất khi TikTok thay đổi:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
```

Cấu trúc: `launch.py` quản lý môi trường; `tikdow/app.py` giao diện và tiến trình tải; `tikdow/core.py` settings, kiểm tra URL, tạo lệnh; `tests/` kiểm thử độc lập mạng.

Bộ tải dựa trên [yt-dlp](https://github.com/yt-dlp/yt-dlp). Không đảm bảo mọi video tải được: video riêng tư, yêu cầu đăng nhập, vùng địa lý hoặc chống bot có thể bị từ chối. Bản đầu chưa hỗ trợ đăng nhập/cookies, album ảnh, LIVE hay tải hàng loạt. Chỉ tải nội dung bạn có quyền sử dụng.

## License

Giữ nguyên GPL-3.0 trong [LICENSE](LICENSE).
