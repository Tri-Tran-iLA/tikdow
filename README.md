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

## Âm thanh và ngôn ngữ / Audio and language

Chọn **Tiếng Việt / English** ở góc trên bên phải để đổi giao diện ngay. Lựa chọn được lưu cho lần mở sau. Thông báo của TikDow được dịch; log gốc từ yt-dlp/FFmpeg giữ nguyên để hỗ trợ chẩn đoán.

- **Giữ nguyên / Original**: tải như trước, không đo hay chỉnh âm thanh.
- **Chỉ phân tích / Analyze only**: đo Integrated LUFS, true peak (dBTP), loudness range (LU) và hiện trong nhật ký.
- **Nâng loudness / Enhance loudness** (mặc định): đo trước, xử lý hai lượt bằng FFmpeg `loudnorm`, đo lại bản xuất. Chọn −16 / −14 / −12 LUFS (nhẹ / cân bằng / mạnh), mặc định −14.
- **Kiểm tra file có sẵn / Check local file**: áp dụng cho MP3/MP4 trên máy. Khi chọn Giữ nguyên, nút này chỉ phân tích. Bản xử lý được lưu cạnh file đã chọn; Mở thư mục trỏ tới thư mục đó.

Bản gốc luôn được giữ. Bản mới có hậu tố `.loudness.mp3` hoặc `.loudness.mp4`; các lần xuất sau thêm số, không ghi đè. MP4 sao chép luồng video, chỉ mã hóa lại âm thanh AAC; MP3 mã hóa lại theo bitrate đã chọn. "Gốc" ở đây là file đã tải/chọn trước xử lý, không phải bản master người đăng tải lên TikTok. Với MP3, phép đo diễn ra sau bước trích xuất MP3 của yt-dlp.

Ưu tiên tăng gain tuyến tính để giữ độ động; FFmpeg có thể chuyển sang xử lý động khi cần giới hạn peak. Giới hạn tăng tối đa 12 dB, bỏ qua im lặng/không đo được và file đã đạt mức đích (dung sai 0,5 LU). Bộ lọc đặt −2 dBTP để chừa khoảng cho mã hóa; bản MP3/AAC sau giải mã được đo lại và chỉ xuất khi true peak ≤ −1 dBTP. Nếu cần sẽ giảm gain và mã hóa lại từ nguồn, tối đa 4 lần. Vì thế mức LUFS thực tế có thể thấp hơn mức đích. Lỗi/hủy dọn file xử lý tạm, giữ nguồn.

Đây là tăng độ lớn cảm nhận, không khôi phục chi tiết đã mất hoặc giả lập EQ/hiệu ứng phát của TikTok. Các mức LUFS trên là lựa chọn của ứng dụng, không phải thông số công bố của TikTok. Tài liệu kỹ thuật: [FFmpeg loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm).

**English:** Choose English at the top right; the choice persists. Original downloads unchanged; Analyze only reports integrated LUFS, true peak and loudness range; Enhance creates a separate normalized copy. The default target is −14 LUFS, with −16 and −12 available. Original files are never overwritten. Boost is capped at 12 dB; silent/unmeasurable or already-loud audio is skipped. Encoded output is remeasured and must pass a −1 dBTP ceiling, which takes priority over the loudness target. MP4 video is stream-copied. The local-file button works with existing MP3/MP4 files. This measures downloaded media, not TikTok's upload master or playback processing.

## Settings JSON

Tự lưu tại **`settings/settings.json`** khi đổi lựa chọn, rời ô nhập, bắt đầu tải hoặc đóng ứng dụng:

- `format`: mp3/mp4.
- `output_dir`: thư mục đích; mặc định `~/Downloads/TikDow`.
- `mp3_bitrate`: bitrate MP3.
- `ffmpeg_dir`: thư mục chứa FFmpeg và FFprobe, trống để tìm trong PATH.
- `language`: `vi` / `en`, mặc định `vi`.
- `audio_mode`: `original` / `analyze` / `enhance`, mặc định `enhance`.
- `target_lufs`: chuỗi `-16` / `-14` / `-12`, mặc định `-14`. Settings cũ tự bổ sung các trường mới.

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

Cấu trúc: `launch.py` quản lý môi trường; `tikdow/app.py` giao diện và tiến trình tải; `tikdow/core.py` settings, kiểm tra URL, tạo lệnh; `tikdow/audio.py` phân tích/xử lý âm thanh; `tikdow/i18n.py` tài nguyên Việt/Anh; `tests/` kiểm thử độc lập mạng. Các bài kiểm tra âm thanh dùng FFmpeg thật, tự bỏ qua nếu chưa cài FFmpeg/FFprobe.

Bộ tải dựa trên [yt-dlp](https://github.com/yt-dlp/yt-dlp). Không đảm bảo mọi video tải được: video riêng tư, yêu cầu đăng nhập, vùng địa lý hoặc chống bot có thể bị từ chối. Bản đầu chưa hỗ trợ đăng nhập/cookies, album ảnh, LIVE hay tải hàng loạt. Chỉ tải nội dung bạn có quyền sử dụng.

## License

Giữ nguyên GPL-3.0 trong [LICENSE](LICENSE).
