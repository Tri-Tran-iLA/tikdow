from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if sys.prefix == sys.base_prefix or Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
    raise SystemExit('TikDow requires its own .venv. Run: python launch.py')

from .app import App
App().mainloop()
