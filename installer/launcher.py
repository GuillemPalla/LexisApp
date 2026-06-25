import subprocess
import os
import sys

# When bundled by PyInstaller, use sys.executable to get the real .exe location
base = os.path.dirname(sys.executable)
bat = os.path.join(base, "launch.bat")
subprocess.Popen(["cmd.exe", "/c", bat], cwd=base)