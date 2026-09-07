"""Measure and normalize audio, keeping the downloaded file untouched."""
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


def measure(source, ffmpeg, target):
    result = subprocess.run([ffmpeg, '-hide_banner', '-nostdin', '-i', str(source),
        '-map', '0:a:0', '-af', f'loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json',
        '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    matches = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', result.stderr, re.S)
    if not matches:
        raise RuntimeError('FFmpeg did not return loudness measurements.')
    return json.loads(matches[-1])


def normalize(source, settings, emit=print):
    source = Path(source).resolve()
    target = settings.get('target_lufs', '-14')
    if target not in ('-16', '-14', '-12'):
        raise ValueError('Invalid LUFS target')
    ffmpeg = shutil.which('ffmpeg', path=settings['ffmpeg_dir'] or None)
    if not ffmpeg:
        raise RuntimeError('FFmpeg not found')
    vi = settings.get('language', 'vi') == 'vi'
    emit('Đang đo âm thanh nguồn…' if vi else 'Measuring source audio…')
    measured = measure(source, ffmpeg, target)
    emit(f"{'Nguồn' if vi else 'Source'}: {measured['input_i']} LUFS | True peak: {measured['input_tp']} dBTP | LRA: {measured['input_lra']} LU")
    if not all(math.isfinite(float(measured[k])) for k in ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset')):
        emit('Âm thanh im lặng/quá ngắn để chuẩn hóa. Giữ nguyên file nguồn.' if vi else 'Silent/too short to normalize. Original file retained.')
        return None
    emit('Đang chuẩn hóa loudness…' if vi else 'Normalizing loudness…')
    filt = (f'loudnorm=I={target}:TP=-1.5:LRA=11:linear=true'
            f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
            f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
            f":offset={measured['target_offset']}")
    output = source.with_name(f'{source.stem}.loudness_{target}LUFS_{uuid.uuid4().hex[:8]}{source.suffix}')
    # A private staging directory prevents partial output from appearing complete.
    with tempfile.TemporaryDirectory(prefix='.tikdow-loudness-', dir=source.parent) as temp:
        staged = Path(temp) / ('output' + source.suffix)
        command = [ffmpeg, '-hide_banner', '-nostdin', '-v', 'error', '-i', str(source)]
        if source.suffix.lower() == '.mp4':
            command += ['-map', '0:v:0?', '-map', '0:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart']
        else:
            command += ['-map', '0:a:0', '-vn', '-c:a', 'libmp3lame', '-b:a', settings['mp3_bitrate'] + 'k']
        command += ['-af', filt, '-ar', '48000', str(staged)]
        subprocess.run(command, check=True)
        emit('Đang đo file đã xuất…' if vi else 'Measuring encoded output…')
        after = measure(staged, ffmpeg, target)
        emit(f"{'Kết quả' if vi else 'Result'}: {after['input_i']} LUFS | True peak: {after['input_tp']} dBTP")
        staged.replace(output)
    emit(f"{'Đã lưu' if vi else 'Saved'}: {output}")
    return output


if __name__ == '__main__':
    try:
        normalize(sys.argv[1], json.loads(sys.argv[2]), lambda s: print(s, flush=True))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
