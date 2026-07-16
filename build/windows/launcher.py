"""
Tiny wrapper compiled to launcher.exe by PyInstaller.

Its only job is to give the Start Menu / Desktop shortcut a proper icon and
a truly silent launch. It does NOT run launch.bat directly, because
launching a .bat via cmd.exe /c always briefly flashes a console window,
even from a --noconsole PyInstaller exe. Instead it hands off to
launch.vbs, which runs launch.bat with WScript's hidden window style (0),
so nothing ever flashes on screen.
"""
import subprocess
import os
import sys

# When bundled by PyInstaller, sys.executable is the real launcher.exe path,
# which lives at the root of the installed app (next to launch.vbs/launch.bat).
base = os.path.dirname(sys.executable)
vbs = os.path.join(base, "launch.vbs")

subprocess.Popen(["wscript.exe", vbs], cwd=base)
