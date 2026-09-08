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
                    'https://tiktok.com/', 'https://www.tiktok.com/@x/live'):
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


class PhotoTests(unittest.TestCase):
    def test_photo_forces_mp3_and_keeps_post_id(self):
        from tikdow.core import is_photo_url
        url = 'https://www.tiktok.com/@mcquinnt6/photo/7672950905859263762'
        self.assertTrue(is_photo_url(url))
        command = build_command(url, defaults())
        self.assertIn('--audio-format', command)
        self.assertIn('mp3', command)
        self.assertNotIn('--recode-video', command)
        self.assertEqual(command[-1], url.replace('/photo/', '/video/'))

    def test_photo_detection_ignores_query_and_fake_domain(self):
        from tikdow.core import is_photo_url
        for url in ('https://evil.test/@x/photo/123',
                    'https://www.tiktok.com/@x/video/123?ref=/photo/123',
                    'https://vt.tiktok.com/abc'):
            self.assertFalse(is_photo_url(url))
        self.assertTrue(is_photo_url('https://m.tiktok.com/@x/photo/123/?lang=en'))

    def test_ui_restores_previous_format(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from tikdow.app import App
        import tkinter as tk
        root = tk.Tcl()
        app = SimpleNamespace(url=tk.StringVar(root, 'https://www.tiktok.com/@x/photo/123'),
            values={'format':tk.StringVar(root, 'mp4')}, photo_mode=False, previous_format='mp4',
            mp4_button=Mock(), status=Mock(), display=SimpleNamespace(last=('monitor', 96)),
            t=lambda s:s, persist=Mock())
        app.mp4_button.master.pack_slaves.return_value=[Mock()]
        App.update_photo_mode(app)
        self.assertEqual(app.values['format'].get(),'mp3')
        app.mp4_button.pack_forget.assert_called_once()
        self.assertEqual(app.display.last, ('monitor', 96))
        App.update_photo_mode(app, resolved_photo=True)
        app.mp4_button.pack_forget.assert_called_once()
        app.persist.assert_called_once()
        app.url.set('https://www.tiktok.com/@x/video/123')
        App.update_photo_mode(app)
        self.assertEqual(app.values['format'].get(),'mp4')
        app.mp4_button.pack.assert_called_once()
        self.assertEqual(app.display.last, ('monitor', 96))
