import os
import webbrowser
import subprocess
import pystray
from PIL import Image

def get_icon():
    # Use the existing icon.ico, or create a simple fallback
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    # Minimal fallback: a plain coloured square
    img = Image.new("RGB", (64, 64), color=(94, 11, 167))
    return img

def quit_app(icon, item):
    icon.stop()
    # Terminate the current process and all its child processes
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(os.getpid())],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

def run_tray():
    icon = pystray.Icon(
        "Lexis",
        get_icon(),
        "Lexis",
        menu=pystray.Menu(
            pystray.MenuItem("Open", lambda icon, item: webbrowser.open("http://localhost:8000"), default=True),
            pystray.MenuItem("Quit", quit_app),
        )
    )
    icon.run()