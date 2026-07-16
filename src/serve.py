from pathlib import Path
import sys
import os
import threading
from textual_serve.server import Server

app_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(app_dir))

from tray import run_tray

app_path = app_dir / "app.py"
python = sys.executable

os.chdir(app_dir)
os.environ["PYTHONPATH"] = str(app_dir)

threading.Thread(target=run_tray, daemon=True).start()

Server(f'"{python}" "{app_path}"', title="Starting Lexis (this may take a while)...").serve()