"""Settings, URL validation and downloader command construction."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import urlsplit
from .i18n import tr

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = ROOT / 'settings' / 'settings.json'


def defaults():
    return {'format': 'mp4', 'output_dir': str(Path.home() / 'Downloads' / 'TikDow'),
            'mp3_bitrate': '192', 'ffmpeg_dir': '', 'language': 'vi',
            'audio_mode': 'enhance', 'target_lufs': '-14'}


def load_settings(path=SETTINGS_FILE):
    settings = defaults()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return settings
    if not isinstance(data, dict):
        return settings
    for key in settings:
        if isinstance(data.get(key), str):
            settings[key] = data[key]
    if settings['format'] not in ('mp3', 'mp4'):
        settings['format'] = 'mp4'
    if settings['mp3_bitrate'] not in ('128', '192', '256', '320'):
        settings['mp3_bitrate'] = '192'
    if not settings['output_dir'].strip():
        settings['output_dir'] = defaults()['output_dir']
    for key, allowed in {'language': ('vi', 'en'), 'audio_mode': ('original', 'analyze', 'enhance'),
                         'target_lufs': ('-16', '-14', '-12')}.items():
        if settings[key] not in allowed:
            settings[key] = defaults()[key]
    return settings


def save_settings(settings, path=SETTINGS_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         delete=False, suffix='.tmp') as handle:
            name = handle.name
            json.dump(settings, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def validate_url(url, language='vi'):
    url = url.strip()
    try:
        parts = urlsplit(url)
        valid = (parts.scheme == 'https' and
                 parts.hostname in ('tiktok.com', 'www.tiktok.com', 'm.tiktok.com',
                                    'vm.tiktok.com', 'vt.tiktok.com') and
                 parts.port in (None, 443) and not parts.username and not parts.password and
                 bool(parts.path.strip('/')) and not any(c.isspace() for c in url))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError(tr(language, 'invalid_url'))
    if '/photo/' in parts.path or '/live' in parts.path:
        raise ValueError(tr(language, 'video_only'))
    return url


def check_ffmpeg(directory, language='vi'):
    for tool in ('ffmpeg', 'ffprobe'):
        found = shutil.which(tool, path=directory) if directory else shutil.which(tool)
        if not found:
            raise ValueError(tr(language, 'missing_ffmpeg'))


def build_command(url, settings):
    url = validate_url(url, settings.get('language', 'vi'))
    command = [sys.executable, '-m', 'yt_dlp', '--ignore-config', '--no-playlist',
               '--newline', '--no-color', '--progress', '--windows-filenames',
               '--socket-timeout', '20', '--retries', '3', '--no-overwrites',
               '-P', settings['output_dir'], '-o', '%(title).100s [%(id)s].%(ext)s']
    command += ['--no-simulate', '--print', 'after_move:TIKDOW_FILE:%(filepath)j']
    if settings['ffmpeg_dir']:
        command += ['--ffmpeg-location', settings['ffmpeg_dir']]
    if settings['format'] == 'mp3':
        command += ['-f', 'bestaudio/best', '-x', '--audio-format', 'mp3',
                    '--audio-quality', settings['mp3_bitrate'] + 'K']
    else:
        command += ['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    '--merge-output-format', 'mp4', '--recode-video', 'mp4']
    return command + ['--', url]
