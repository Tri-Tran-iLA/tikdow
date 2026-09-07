"""Cancellable FFmpeg analysis and two-pass loudness enhancement.

Input is the downloaded/local media, not TikTok's original upload master.
Never overwrite the input. Verify the decoded lossy output before publishing it.
"""
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile

from .i18n import tr


class Cancelled(Exception):
    pass


def terminate(process):
    if process.poll() is not None:
        return
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.killpg(process.pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        pass


class AudioProcessor:
    def __init__(self, settings, cancelled, emit, set_process=lambda p: None):
        self.settings = settings
        self.cancelled = cancelled
        self.emit = emit
        self.set_process = set_process
        self.language = settings.get('language', 'vi')
        self.target = float(settings.get('target_lufs', '-14'))
        if self.target not in (-16, -14, -12):
            raise ValueError('Invalid target LUFS')

    def say(self, key, **values):
        self.emit(tr(self.language, key, **values))

    def check_cancel(self):
        if self.cancelled.is_set():
            raise Cancelled()

    def run(self, tool, arguments):
        self.check_cancel()
        executable = shutil.which(tool, path=self.settings['ffmpeg_dir'] or None)
        if not executable:
            raise ValueError(tr(self.language, 'missing_ffmpeg'))
        kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {'start_new_session': True}
        # File-backed capture avoids pipe deadlock and unbounded diagnostic buffers.
        with tempfile.TemporaryFile() as output:
            with subprocess.Popen([executable, *arguments], stdout=output, stderr=output,
                                  stdin=subprocess.DEVNULL, **kwargs) as process:
                self.set_process(process)
                try:
                    while process.poll() is None:
                        if self.cancelled.wait(0.1):
                            terminate(process)
                            try:
                                process.wait(timeout=3)
                            except subprocess.TimeoutExpired:
                                process.kill()
                            raise Cancelled()
                    self.check_cancel()
                    output.seek(0, os.SEEK_END)
                    output.seek(max(0, output.tell() - 65536))
                    text = output.read().decode('utf-8', errors='replace')
                    if process.returncode:
                        raise RuntimeError(text[-3000:])
                    return text
                finally:
                    self.set_process(None)

    def measure(self, source, target=None, peak=-2.0):
        text = self.run('ffmpeg', ['-hide_banner', '-nostdin', '-nostats', '-i', str(source),
            '-map', '0:a:0', '-vn', '-af',
            f'loudnorm=I={self.target if target is None else target}:TP={peak}:LRA=50:print_format=json',
            '-f', 'null', '-'])
        for block in reversed(re.findall(r'\{[^{}]*\}', text)):
            try:
                data = json.loads(block)
                result = {key: float(data[key]) for key in
                          ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset')}
                return result
            except (ValueError, KeyError, TypeError):
                continue
        raise ValueError(tr(self.language, 'bad_measurement'))

    def stats(self, key, measured):
        self.say(key, i=measured['input_i'], tp=measured['input_tp'], lra=measured['input_lra'])

    def process(self, source):
        source = Path(source).resolve(strict=True)
        self.say('measuring')
        probe = json.loads(self.run('ffprobe', ['-v', 'error', '-select_streams', 'a:0',
                          '-show_entries', 'stream=sample_rate', '-of', 'json', str(source)]))
        if not probe.get('streams'):
            self.say('no_audio')
            return None
        original = self.measure(source)
        self.stats('source_stats', original)
        if self.settings.get('audio_mode') != 'enhance':
            return None
        if not all(math.isfinite(v) for v in original.values()) or original['input_i'] < -70:
            self.say('quiet')
            return None
        if original['input_i'] >= self.target - 0.5:
            self.say('enough')
            return None
        # Do not amplify near-silence/background noise by dozens of dB.
        target = min(self.target, original['input_i'] + 12)
        target = max(-70, target)
        if target != self.target:
            original = self.measure(source, target)
        self.say('limited')
        self.say('normalizing')
        measured_filter = (f'loudnorm=I={target}:TP=-2:LRA=50:'
            f'measured_I={original["input_i"]}:measured_TP={original["input_tp"]}:'
            f'measured_LRA={original["input_lra"]}:measured_thresh={original["input_thresh"]}:'
            f'offset={original["target_offset"]}:linear=true')
        suffix = source.suffix.lower()
        if suffix not in ('.mp3', '.mp4'):
            raise ValueError('MP3 / MP4 only')
        # Same filesystem for atomic publication; temporary outputs disappear on failure/cancel.
        with tempfile.TemporaryDirectory(prefix='.tikdow-audio-', dir=source.parent) as folder:
            staged = Path(folder) / ('processed' + suffix)
            attenuation = 0.0
            result = None
            for _ in range(4):
                self.check_cancel()
                af = measured_filter + (f',volume=-{attenuation}dB' if attenuation else '')
                command = ['-hide_banner', '-nostdin', '-nostats', '-y', '-i', str(source)]
                if suffix == '.mp4':
                    command += ['-map', '0:v:0?', '-map', '0:a:0', '-c:v', 'copy',
                                '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart']
                else:
                    command += ['-map', '0:a:0', '-vn', '-c:a', 'libmp3lame',
                                '-b:a', self.settings['mp3_bitrate'] + 'k']
                rate = probe['streams'][0].get('sample_rate', '48000')
                if rate not in ('32000', '44100', '48000'):
                    rate = '48000'
                command += ['-map_metadata', '0', '-af', af, '-ar', rate, str(staged)]
                self.run('ffmpeg', command)
                self.say('verifying')
                result = self.measure(staged)
                if math.isfinite(result['input_tp']) and result['input_tp'] <= -1.0:
                    break
                if not math.isfinite(result['input_tp']):
                    raise ValueError(tr(self.language, 'peak_error'))
                attenuation += result['input_tp'] + 1.2
            else:
                raise ValueError(tr(self.language, 'peak_error'))
            self.check_cancel()
            # Reserve a unique destination so repeated runs never overwrite earlier exports.
            destination = source.with_name(source.stem + '.loudness' + suffix)
            counter = 1
            while True:
                try:
                    with destination.open('xb'):
                        pass
                    break
                except FileExistsError:
                    destination = source.with_name(f'{source.stem}.loudness-{counter}{suffix}')
                    counter += 1
            try:
                self.check_cancel()
                os.replace(staged, destination)
            except BaseException:
                destination.unlink(missing_ok=True)
                raise
        self.stats('output_stats', result)
        self.say('saved', path=destination)
        return destination
