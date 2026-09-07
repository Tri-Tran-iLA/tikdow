import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tikdow.core import defaults, load_settings
from tikdow.i18n import STRINGS, translate
from tikdow.loudness import measure, normalize


class PreferencesTests(unittest.TestCase):
    def test_old_and_invalid_settings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'settings.json'
            p.write_text(json.dumps({'format':'mp3', 'language':'xx', 'loudness':True, 'target_lufs':'0'}))
            s = load_settings(p)
            self.assertEqual((s['format'],s['language'],s['loudness'],s['target_lufs']), ('mp3','vi','off','-14'))

    def test_translations(self):
        for vi, en in STRINGS.items():
            self.assertTrue(en)
            self.assertEqual(translate(vi, 'vi'), vi)
            self.assertEqual(translate(vi, 'en'), en)


@unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg required')
class AudioIntegrationTests(unittest.TestCase):
    def test_mp3_mp4_measure_normalize_and_preserve_original(self):
        with tempfile.TemporaryDirectory() as d:
            for ext in ('mp3', 'mp4'):
                source = Path(d) / ('Âm thanh test.' + ext)
                cmd = ['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=5']
                if ext == 'mp4':
                    cmd += ['-f','lavfi','-i','color=size=64x64:rate=10:duration=5','-c:v','libx264','-c:a','aac']
                cmd += ['-af','volume=0.1',str(source)]
                subprocess.run(cmd, check=True)
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                before = measure(source, 'ffmpeg', '-14')
                out = normalize(source, defaults(), emit=lambda _: None)
                after = measure(out, 'ffmpeg', '-14')
                self.assertLess(float(before['input_i']), -30)
                self.assertAlmostEqual(float(after['input_i']), -14, delta=1)
                self.assertLess(float(after['input_tp']), 0)
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)
                if ext == 'mp4':
                    def video_hash(path):
                        return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-c','copy','-f','hash','-'])
                    self.assertEqual(video_hash(source),video_hash(out))

    def test_silence_is_not_amplified(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'silent.mp3'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','3',str(source)],check=True)
            self.assertIsNone(normalize(source, defaults(), emit=lambda _: None))
            self.assertTrue(source.exists())
