"""Create and exclusively use this project's virtual environment."""
import hashlib
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv'
PYTHON = ENV / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError('TikDow requires Python 3.10 or newer.')
    if not PYTHON.exists():
        print('Creating .venv ...', flush=True)
        venv.EnvBuilder(with_pip=True).create(ENV)
    requirement = ROOT / 'requirements.txt'
    digest = hashlib.sha256(requirement.read_bytes()).hexdigest()
    stamp = ENV / '.tikdow-requirements'
    ready = subprocess.run([str(PYTHON), '-c', 'import yt_dlp; import tkinter; import curl_cffi'],
                           capture_output=True).returncode == 0
    if not ready or not stamp.exists() or stamp.read_text() != digest:
        subprocess.run([str(PYTHON), '-m', 'pip', 'install', '--upgrade', '-r', str(requirement)], check=True)
        subprocess.run([str(PYTHON), '-c', 'import yt_dlp; import tkinter; import curl_cffi'], check=True)
        stamp.write_text(digest)
    return subprocess.call([str(PYTHON), '-m', 'tikdow'], cwd=ROOT)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'Could not start TikDow: {error}', file=sys.stderr)
        sys.exit(1)
