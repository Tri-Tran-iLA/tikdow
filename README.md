# TikDow 1.0

**Tải video TikTok thành MP4 hoặc MP3, kèm chuẩn hóa loudness và giao diện English / Tiếng Việt.**

Ứng dụng desktop Python dành chủ yếu cho Windows, phát triển bởi [Tri-Tran-iLA](https://github.com/Tri-Tran-iLA).

[Repository](https://github.com/Tri-Tran-iLA/tikdow) · [Báo lỗi](https://github.com/Tri-Tran-iLA/tikdow/issues) · [English](#english) · [GPL-3.0](LICENSE)

## Tính năng

- **MP4 / MP3:** hỗ trợ link video đầy đủ và link rút gọn `vt.tiktok.com`, `vm.tiktok.com`; MP3 chọn 128 / 192 / 256 / 320 kbps.
- **Loudness:** đo nguồn và kết quả, chuẩn hóa theo −16 / −14 / −12 LUFS, lưu thêm bản riêng và giữ bản tải ban đầu.
- **Giao diện song ngữ:** chuyển English / Tiếng Việt ngay trong ứng dụng, không cần khởi động lại.
- **DPI tự động:** bố cục cho Full HD, QHD/2K và 4K; tự điều chỉnh theo DPI và vùng làm việc khi đổi màn hình. Khóa resize/maximize, vẫn di chuyển và thu nhỏ được.
- **Tải nền:** thanh tiến trình, nhật ký, hủy tải/xử lý và mở thư mục kết quả.
- **Môi trường riêng:** launcher tự tạo và bắt buộc chạy trong `.venv` của dự án.
- **Nhớ cấu hình:** tự lưu lựa chọn vào JSON; liên kết tác giả và repo ở cuối giao diện.

## Cài đặt và khởi chạy

Cần **Python 3.10+** có pip, Tcl/Tk; **FFmpeg và FFprobe**; **Git** nếu dùng lệnh clone. Khi cài Python, chọn **Add Python to PATH**. Tải FFmpeg từ [trang chính thức](https://ffmpeg.org/download.html), thêm thư mục `bin` vào PATH hoặc chọn thư mục đó trong TikDow.

```powershell
git clone https://github.com/Tri-Tran-iLA/tikdow.git
cd tikdow
.\Start-TikDow.bat
```

Hoặc tải **Code → Download ZIP**, giải nén vào thư mục có quyền ghi rồi nhấp đúp `Start-TikDow.bat`.

Lần đầu cần Internet để tạo `.venv` và cài thư viện. Những lần sau dùng lại môi trường; launcher kiểm tra dependencies và cài/cập nhật khi cần. Không cần tự activate và không cài thư viện vào Python hệ thống.

Có thể khởi chạy bằng `python launch.py`. Linux/macOS dùng `python3 launch.py`, cần Tkinter, venv và FFmpeg; Windows là nền tảng mục tiêu chính.

## Sử dụng

1. Dán link video TikTok.
2. Chọn **MP4** hoặc **MP3**, bitrate MP3 và thư mục lưu.
3. Nếu muốn chuẩn hóa âm lượng, bật **Nâng loudness (lưu thêm bản riêng)** rồi chọn LUFS.
4. Bấm **Tải xuống**. Xem tiến trình/nhật ký, hoặc bấm **Hủy tải** để dừng.
5. Bấm **Mở thư mục** để xem kết quả.

Chọn **English** hoặc **Tiếng Việt** ở góc trên bên phải. Nhật ký kỹ thuật từ yt-dlp/FFmpeg giữ ngôn ngữ gốc. Khi đóng ứng dụng, hãy chờ tải/xử lý hoàn tất hoặc hủy và đợi dừng.

### Chuẩn hóa loudness

Loudness **mặc định tắt**. Khi bật, TikDow đo integrated loudness, true peak và LRA của file tải về, chạy FFmpeg `loudnorm` hai lượt theo số đo, rồi đo lại file đã mã hóa.

| Lựa chọn | Giá trị |
| --- | --- |
| Loudness mục tiêu | −16 / **−14 mặc định** / −12 LUFS |
| True peak mục tiêu | −1.5 dBTP |
| LRA mục tiêu | 11 LU |
| MP3 đã chuẩn hóa | Bitrate đã chọn, 48 kHz |
| MP4 đã chuẩn hóa | Giữ luồng video; âm thanh AAC 256 kbps, 48 kHz |
| Tên bản xuất riêng | `<tên>.loudness_<LUFS>LUFS_<id>.mp3` hoặc `.mp4` |

Chuẩn hóa có thể tăng **hoặc giảm** âm lượng tùy nguồn. File tải ban đầu được giữ nguyên; file im lặng hoặc không đủ số đo được bỏ qua. FFmpeg có thể dùng xử lý động nếu giới hạn đỉnh/dải động không cho phép chuẩn hóa tuyến tính. Mã hóa có mất dữ liệu có thể làm kết quả lệch nhẹ mục tiêu; số đo cuối hiển thị trong log.

Tính năng này không tái tạo hiệu ứng phát của TikTok hay phục hồi chất lượng đã mất. Nguồn phân tích là file tải về, không phải bản master của tác giả.

## Cấu hình

File **`settings/settings.json`** được tạo tự động và không đưa lên Git. Có mẫu tại [settings/settings.example.json](settings/settings.example.json).

| Trường | Giá trị mặc định | Ý nghĩa |
| --- | --- | --- |
| `format` | `mp4` | Định dạng tải |
| `output_dir` | `~/Downloads/TikDow` | Thư mục lưu |
| `mp3_bitrate` | `192` | Bitrate MP3, kbps |
| `ffmpeg_dir` | Chuỗi trống | Tìm FFmpeg/FFprobe trong PATH hoặc dùng thư mục chỉ định |
| `language` | `vi` | `vi` / `en` |
| `loudness` | `off` | `off` / `on` |
| `target_lufs` | `-14` | `-16` / `-14` / `-12` |

Cấu hình được ghi qua file tạm rồi thay thế nguyên tử; trường thiếu/sai dùng mặc định. Link đã dán không được lưu. Nếu chuyển dự án sang máy khác hoặc thay bản Python, tạo lại `.venv` bằng launcher; vẫn giữ được JSON.

## Cập nhật và xử lý sự cố

Đóng ứng dụng trước khi cập nhật:

```powershell
git pull --ff-only
.\Start-TikDow.bat
```

Nếu TikTok thay đổi và bộ tải gặp lỗi, cập nhật dependencies trong môi trường của ứng dụng:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
```

- **Thiếu FFmpeg/FFprobe:** chọn thư mục `bin` chứa cả hai chương trình.
- **Lỗi impersonation:** dependencies đã bao gồm `curl_cffi`; dùng lệnh cập nhật trên để sửa môi trường.
- **Không tải được video:** phiên bản này chưa hỗ trợ đăng nhập/cookies, album ảnh, LIVE hoặc tải hàng loạt. Nội dung riêng tư, giới hạn vùng và chống bot có thể bị từ chối.
- **Scale Windows rất cao:** ứng dụng giảm tỉ lệ UI nếu cần để vừa vùng làm việc; chữ có thể nhỏ hơn mức scale Windows yêu cầu.
- **Buộc dừng khi xử lý:** có thể còn thư mục `.tikdow-loudness-*`; chỉ xóa sau khi ứng dụng đã dừng.

Khi [báo lỗi](https://github.com/Tri-Tran-iLA/tikdow/issues), gửi log lỗi, phiên bản Python, kết quả `git log -1 --oneline` và mức scale Windows nếu lỗi giao diện. Chỉ tải nội dung bạn có quyền sử dụng.

## Phát triển

Phiên bản mã nguồn: **`1.0.0`**.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q tikdow launch.py
```

| Thành phần | Vai trò |
| --- | --- |
| `launch.py` | Tạo/kiểm tra `.venv` và khởi chạy |
| `tikdow/app.py` | UI, tiến trình tải và điều phối xử lý |
| `tikdow/core.py` | JSON, kiểm tra URL và lệnh tải |
| `tikdow/loudness.py` | Đo và chuẩn hóa âm thanh |
| `tikdow/i18n.py` | Chuỗi giao diện song ngữ |
| `tikdow/display.py` | DPI và bố cục cửa sổ |
| `tests/` | Kiểm thử logic và tích hợp FFmpeg |

Kiểm thử bao gồm MP3/MP4, giữ file gốc/luồng video, im lặng, settings, tính toán DPI 100–300% trên Full HD/QHD/4K và khôi phục khi đọc màn hình thất bại. Không thay thế kiểm tra tải TikTok thực tế và giao diện trên Windows đa màn hình.

## English

**TikDow 1.0** is a Python desktop TikTok downloader with MP4/MP3 output, optional loudness normalization, and an English/Vietnamese interface.

**Setup:** install Python 3.10+ with pip and Tcl/Tk, plus FFmpeg and FFprobe. Clone this repository or extract its ZIP, then run `Start-TikDow.bat`. The launcher creates and requires a project-local `.venv`; it installs dependencies automatically. Choose your FFmpeg bin folder in the app if it is not on PATH. Windows is the primary target; Linux/macOS can use `python3 launch.py` with the required system packages.

**Download:** paste a TikTok video URL, choose MP4 or MP3, select an output folder, and click Download. MP3 supports 128/192/256/320 kbps. Progress, cancellation and an Open folder button are included. Select English or Tiếng Việt at the top right; engine logs keep their original language.

**Loudness:** enable normalization before downloading and select −16, −14 or −12 LUFS. TikDow measures the downloaded audio, applies measured two-pass FFmpeg loudnorm processing, then measures the encoded output. Targets are −1.5 dBTP true peak and 11 LU LRA. It retains the original and saves a separate `.loudness_<LUFS>LUFS_<id>` file. MP4 video is stream-copied, with AAC 256 kbps audio; MP3 uses your selected bitrate. Both normalize to 48 kHz. Normalization is off by default and may raise or lower level. It does not recreate TikTok playback effects or recover lost quality; lossy encoding can slightly change final measurements. Silent/unmeasurable audio is skipped.

**Display and settings:** the window cannot be manually resized or maximized, but can be moved/minimized. DPI-aware layout adapts to Full HD, QHD and 4K working areas, reducing effective scale when needed to fit. Preferences persist in `settings/settings.json`; pasted URLs are not saved. Author and repository links appear in the footer.

**Updates:** close TikDow, run `git pull --ff-only`, then start it again. To refresh the downloader, run `.\.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt`. Browser impersonation dependencies are included. Login/cookies, photo albums, LIVE and batch downloads are not supported; private videos, regional restrictions or anti-bot responses may prevent downloads. Forced termination can leave a `.tikdow-loudness-*` temporary folder; remove it only after the app has stopped.

**Validation:** automated tests cover audio processing, preferences, DPI calculations and monitor-error recovery. Live TikTok behavior and Windows multi-monitor visual checks still require testing on the target machine. Report issues with logs, Python version and commit ID. Download only content you have permission to use.

## Tác giả và giấy phép / Author and license

**[Tri-Tran-iLA](https://github.com/Tri-Tran-iLA)** · [TikDow repository](https://github.com/Tri-Tran-iLA/tikdow)

TikDow được phân phối theo **[GPL-3.0](LICENSE)**. / TikDow is distributed under **[GPL-3.0](LICENSE)**.

Built with Python/Tkinter, [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/). Audio normalization uses [FFmpeg loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm).
