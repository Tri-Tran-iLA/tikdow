import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tikdow.core import build_command, check_ffmpeg, defaults, load_settings, save_settings, validate_url


class CoreTests(unittest.TestCase):
    def test_links(self):
        for url in ('https://www.tiktok.com/@demo/video/123', 'https://vt.tiktok.com/abc/', 'https://vm.tiktok.com/abc/'):
            self.assertEqual(validate_url(' ' + url + ' '), url)
        for url in ('https://tiktok.com.evil.org/a', 'https://evil.org/a', 'file:///tmp/a',
                    'https://user@tiktok.com/a', 'https://tiktok.com:bad/a',
                    'https://tiktok.com/', 'https://www.tiktok.com/@x/photo/123'):
            with self.assertRaises(ValueError, msg=url):
                validate_url(url)

    def test_settings_roundtrip_and_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings' / 'settings.json'
            data = defaults() | {'format': 'mp3', 'output_dir': str(Path(folder) / 'Nhạc Việt')}
            save_settings(data, path)
            self.assertEqual(load_settings(path), data)
            path.write_text('{broken')
            self.assertEqual(load_settings(path), defaults())
            path.write_text(json.dumps({'format': 'exe', 'mp3_bitrate': 320, 'output_dir': None}))
            self.assertEqual(load_settings(path), defaults())

    def test_commands(self):
        settings = defaults() | {'output_dir': 'C:/Nhạc Việt', 'ffmpeg_dir': 'C:/FFmpeg/bin'}
        command = build_command('https://vt.tiktok.com/demo/', settings)
        self.assertIn('--recode-video', command)
        self.assertIn('C:/Nhạc Việt', command)
        self.assertEqual(command[-2], '--')
        command = build_command('https://vt.tiktok.com/demo/', settings | {'format': 'mp3'})
        self.assertIn('--audio-format', command)
        self.assertIn('192K', command)
        self.assertNotIn('--recode-video', command)

    def test_ffmpeg_requires_both_tools(self):
        with patch('tikdow.core.shutil.which', side_effect=['/bin/ffmpeg', None]):
            with self.assertRaises(ValueError):
                check_ffmpeg('')


if __name__ == '__main__':
    unittest.main()
