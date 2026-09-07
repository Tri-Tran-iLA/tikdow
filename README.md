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

## v0.2 — Loudness và English / Tiếng Việt

Chọn **English** hoặc **Tiếng Việt** ở góc trên bên phải. Nhãn, nút và thông báo ứng dụng đổi ngay, không cần khởi động lại. Nhật ký kỹ thuật do yt-dlp/FFmpeg trả về giữ ngôn ngữ gốc. Lựa chọn ngôn ngữ được lưu trong settings JSON.

Để nâng âm lượng file tải về:

1. Bật **Nâng loudness (lưu thêm bản riêng)** trước khi tải.
2. Chọn mục tiêu **−16**, **−14** (mặc định) hoặc **−12 LUFS**. Giá trị càng gần 0 càng lớn.
3. Tải như bình thường. TikDow đo integrated loudness, true peak và loudness range của file tải về, sau đó chạy FFmpeg `loudnorm` hai lượt dựa trên số đo.
4. TikDow đo lại âm thanh đã mã hóa và hiện số đo nguồn/kết quả trong nhật ký.
5. Thư mục đích có bản tải ban đầu và bản `.loudness_-14LUFS_<id>.mp3` hoặc `.mp4` (tên đổi theo mục tiêu). ID riêng tránh ghi đè lần xuất trước.

**Mặc định loudness tắt** để không thay đổi âm thanh ngoài ý muốn. Bật lên để dùng chức năng mới. Settings cũ vẫn dùng được; không cần xóa file JSON hay `.venv`.

- True peak mục tiêu: **−1.5 dBTP**, LRA mục tiêu: **11 LU**. FFmpeg ưu tiên chuẩn hóa tuyến tính; có thể dùng xử lý động khi mức đỉnh/dải động không cho phép.
- Chuẩn hóa có thể tăng hoặc giảm âm lượng tùy nguồn. Không phục hồi chất lượng đã mất và không mô phỏng EQ/hiệu ứng phát của TikTok. Nguồn đo là file tải về, không phải master gốc của tác giả.
- MP4 giữ nguyên luồng video, mã hóa lại âm thanh AAC 256 kbps. MP3 dùng bitrate đã chọn. Âm thanh xuất ở 48 kHz.
- Mã hóa có mất dữ liệu có thể làm mức LUFS/true peak cuối lệch nhẹ so với mục tiêu; hãy xem số đo cuối trong log. Không cam kết mọi nguồn đạt chính xác mục tiêu.
- File im lặng hoặc không đủ số đo hữu hạn được bỏ qua, giữ bản tải ban đầu. Nếu xử lý lỗi, bản tải ban đầu vẫn còn.
- Hủy áp dụng cả lúc tải, đo và chuẩn hóa. Nếu buộc dừng tiến trình, thư mục tạm `.tikdow-loudness-*` có thể còn lại; có thể xóa sau khi ứng dụng đã dừng.

Các trường JSON mới: `language` (`vi`/`en`), `loudness` (`off`/`on`), `target_lufs` (`-16`/`-14`/`-12`).

Cập nhật trên Windows (đóng TikDow trước):

```powershell
git pull --ff-only
.\Start-TikDow.bat
```

Thư viện `yt-dlp[default,curl-cffi]` đã bao gồm hỗ trợ browser impersonation. Launcher kiểm tra `curl_cffi` và nâng cấp dependencies khi requirements thay đổi hoặc môi trường cần sửa.

### English quick guide

TikDow is a Python desktop TikTok downloader with **MP3 / MP4 output**, a mandatory project-local **`.venv`**, persistent JSON settings, and a live **English / Vietnamese** language selector.

**Windows setup:** install Python 3.10+ with pip and Tcl/Tk, and FFmpeg plus FFprobe. Clone this repository, then double-click `Start-TikDow.bat`. The launcher creates `.venv` and installs dependencies automatically. Set the FFmpeg bin folder in the app if it is not on PATH. Linux/macOS: use `python3 launch.py` with Tkinter, venv and FFmpeg installed.

**Download:** paste a TikTok video URL, choose MP3 or MP4 and an output folder, then click Download. Browser impersonation dependencies are included, but private videos, login requirements, region restrictions and anti-bot responses can still prevent downloads.

**Loudness:** enable “Normalize loudness (save a separate copy)” and choose −16, −14 or −12 LUFS. TikDow measures the downloaded source, performs measured two-pass FFmpeg loudnorm processing (true peak target −1.5 dBTP, LRA target 11 LU), then measures the encoded result. Both readings appear in the log. Normalization may increase or decrease level; it does not recreate TikTok playback effects or recover lost quality. Silent/unmeasurable audio is skipped.

The original download is retained. The normalized file has a `.loudness_<target>LUFS_<id>` suffix. MP4 video is stream-copied; audio is re-encoded as AAC 256 kbps or MP3 at the selected bitrate, at 48 kHz. Lossy encoding can slightly change final LUFS/true peak. Cancel stops downloading and audio processing; forced termination may leave a `.tikdow-loudness-*` temporary directory that can be removed after stopping the app.

Preferences are saved atomically to `settings/settings.json`: format, output folder, MP3 bitrate, FFmpeg folder, language, loudness enabled state, and LUFS target. Existing settings migrate with safe defaults; normalization is off initially. Engine logs keep their original language.

**Update:** close the app, run `git pull --ff-only`, then launch again. **Tests:** run `python -m unittest discover -s tests -v` inside `.venv`; FFmpeg integration tests cover actual MP3/MP4 loudness, original preservation, MP4 video preservation, and silence handling. Network downloads and Windows visual behavior must be checked on the target machine.

Reference: [FFmpeg loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm).

## v0.3 — Cửa sổ cố định và DPI / Fixed window and DPI

- Khóa kéo resize và nút maximize; vẫn di chuyển, thu nhỏ và đóng cửa sổ bình thường.
- Windows bật Per-Monitor V2 DPI awareness trước khi tạo UI (có fallback cho API Windows cũ).
- Kích thước cơ sở **860 × 800 tại 100%**. Font, padding, khoảng cách và kích thước cửa sổ được scale từ thông số gốc, tránh sai số tích lũy khi đổi màn hình.
- Tự kiểm tra DPI và vùng làm việc của màn hình mỗi 500 ms. Khi kéo sang màn hình có DPI khác hoặc đổi Windows Display Scale, ứng dụng tự tính lại kích thước.
- Hỗ trợ bố cục cho Full HD **1920 × 1080**, QHD/2K **2560 × 1440** và 4K **3840 × 2160**. Độ phân giải và DPI là hai thông số khác nhau: 4K không tự động đồng nghĩa scale 200%.
- Nếu scale quá lớn so với vùng làm việc, toàn bộ UI được giảm tỉ lệ để vừa màn hình và chừa chỗ cho taskbar/thanh tiêu đề. Vì vậy ở Full HD với Windows scale rất cao, chữ có thể nhỏ hơn mức Windows yêu cầu.
- Kiểm thử tính toán: ba độ phân giải trên với scale 100%, 125%, 150%, 175%, 200%, 250%, 300%; vị trí màn hình phụ có tọa độ âm; đổi DPI qua lại không tích lũy sai số. Chưa xác nhận trực quan trên phần cứng Windows đa màn hình thực tế.

**English:** user resizing and maximizing are disabled. The window remains movable and minimizable. On Windows, per-monitor DPI awareness is configured before UI creation. Text, spacing and window dimensions scale from a fixed 860 × 800 baseline at 100%. The app checks the current monitor's DPI and working area every 500 ms and adjusts when moving between displays or changing Windows scaling. The layout fits Full HD, QHD (2560 × 1440) and 4K; at unusually high scaling on a small working area, it reduces the effective UI scale to keep all controls visible. Calculation tests cover 100–300% scaling and negative monitor coordinates; real Windows multi-monitor visual verification remains outstanding.
