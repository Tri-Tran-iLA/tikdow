import hashlib
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from tikdow.audio import AudioProcessor, Cancelled
from tikdow.core import defaults, load_settings
from tikdow.i18n import TEXT, tr
from tikdow.app import App


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class AudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.messages = []
        self.cancel = threading.Event()
        self.processor = AudioProcessor(defaults() | {'language': 'en'}, self.cancel, self.messages.append)

    def fixture(self, name='Nhạc gốc.mp3', volume='0.7', silent=False, video=False):
        source = self.folder / name
        command = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                   'anullsrc=r=48000:cl=stereo' if silent else 'sine=frequency=440:sample_rate=48000']
        if video:
            command += ['-f', 'lavfi', '-i', 'color=c=blue:s=160x90:r=10', '-c:v', 'mpeg4']
        command += ['-t', '5', '-af', f'volume={volume}', str(source)]
        subprocess.run(command, check=True, capture_output=True)
        return source

    def test_boost_and_preserve_original_and_existing_export(self):
        source = self.fixture()
        digest = hashlib.sha256(source.read_bytes()).digest()
        before = self.processor.measure(source)
        result = self.processor.process(source)
        self.assertIsNotNone(result)
        after = self.processor.measure(result)
        self.assertGreater(after['input_i'], before['input_i'] + 5)
        self.assertLessEqual(after['input_tp'], -1)
        self.assertAlmostEqual(after['input_i'], -14, delta=1)
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), digest)
        again = self.processor.process(source)
        self.assertNotEqual(result, again)
        self.assertTrue(result.exists())

    def test_very_quiet_source_boost_is_capped(self):
        source = self.fixture(volume='0.01')
        before = self.processor.measure(source)
        result = self.processor.process(source)
        after = self.processor.measure(result)
        self.assertLessEqual(after['input_i'] - before['input_i'], 12.3)
        self.assertGreater(after['input_i'] - before['input_i'], 10)

    def test_silent_and_loud_sources_not_boosted(self):
        for source in (self.fixture('silent.mp3', silent=True), self.fixture('loud.mp3', volume='4')):
            self.assertIsNone(self.processor.process(source))
        self.assertFalse(list(self.folder.glob('*.loudness*')))

    def test_analysis_and_cancel_do_not_write_output(self):
        source = self.fixture()
        self.processor.settings['audio_mode'] = 'analyze'
        self.assertIsNone(self.processor.process(source))
        self.processor.settings['audio_mode'] = 'enhance'
        self.cancel.set()
        with self.assertRaises(Cancelled):
            self.processor.process(source)
        self.assertFalse(list(self.folder.glob('*.loudness*')))

    def test_cancel_active_process(self):
        timer = threading.Timer(0.2, self.cancel.set)
        timer.start()
        try:
            with self.assertRaises(Cancelled):
                self.processor.run('ffmpeg', ['-v', 'error', '-re', '-f', 'lavfi', '-i',
                    'anullsrc', '-t', '60', '-f', 'null', '-'])
        finally:
            timer.cancel()

    def test_mp4_video_stream_is_unchanged(self):
        source = self.fixture('video.mp4', video=True)
        output = self.processor.process(source)
        self.assertIsNotNone(output)
        def video_hash(path):
            return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                '-map', '0:v:0', '-c', 'copy', '-f', 'hash', '-'])
        self.assertEqual(video_hash(source), video_hash(output))
        self.assertLessEqual(self.processor.measure(output)['input_tp'], -1)

    def test_video_without_audio(self):
        path = self.folder / 'silent-video.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=s=160x90',
                        '-t', '1', '-c:v', 'mpeg4', str(path)], check=True)
        self.assertIsNone(self.processor.process(path))
        self.assertIn(tr('en', 'no_audio'), self.messages)

    def test_encoding_failure_cleans_temporary_files(self):
        source = self.fixture()
        run = self.processor.run
        def fail_encoder(tool, args):
            if '-c:a' in args:
                raise RuntimeError('encoder failure')
            return run(tool, args)
        with patch.object(self.processor, 'run', side_effect=fail_encoder):
            with self.assertRaisesRegex(RuntimeError, 'encoder failure'):
                self.processor.process(source)
        self.assertEqual(list(self.folder.iterdir()), [source])


class IntegrationTests(unittest.TestCase):
    def test_language_and_settings_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            path.write_text(json.dumps({'format': 'mp3', 'language': 'xx', 'target_lufs': '999', 'audio_mode': 'bad'}))
            values = load_settings(path)
            self.assertEqual(values['language'], 'vi')
            self.assertEqual(values['target_lufs'], '-14')
            self.assertEqual(values['audio_mode'], 'enhance')
            self.assertEqual(values['format'], 'mp3')
        for key, pair in TEXT.items():
            self.assertEqual(len(pair), 2, key)
            self.assertTrue(all(pair), key)

    def test_download_worker_uses_final_json_path(self):
        class Worker:
            events = queue.Queue()
            cancelled = threading.Event()
            process = None
            set_process = lambda self, p: setattr(self, 'process', p)
        worker = Worker()
        path = '/tmp/Nhạc [123].mp3'
        command = [sys.executable, '-c', 'print(' + repr('TIKDOW_FILE:' + json.dumps(path)) + ')']
        with patch('tikdow.app.AudioProcessor') as processor:
            App.worker(worker, command, defaults())
            processor.return_value.process.assert_called_once_with(path)
        self.assertEqual(worker.events.get_nowait(), ('done', 0))
