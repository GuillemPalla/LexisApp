# How the LexisApp installer is built

## Build-time pipeline

1. **Source code** — `app.py`, `serve.py`, `tray.py`, `screens/`,
   `tokenizers/`, `icon.ico` all live in `src/`.

2. **Embedded Python runtime** — `python-3.12.2-embed-amd64.zip`
   downloaded from python.org and unzipped into `build/windows/python/`.

   **Unzipping alone is not enough** — the embeddable distribution ships with a
   `python312._pth` file that has `import site` commented out, which
   disables `site-packages` *and* pip entirely. A bare unzip gives you a
   working interpreter that can't `pip install` anything. Two more steps
   are required before dependencies can go in:
   - Edit `python312._pth` and uncomment `import site` — this re-enables
     the standard `Lib\site-packages` lookup relative to the interpreter
   - Run `get-pip.py` against it to bootstrap pip, then
     `python.exe -m pip install -r requirements.txt` to install packages

   This is the Python interpreter that actually ships inside the
   installer and runs on the end user's machine — it's separate from any
   dev Python on your own computer. `build.ps1` automates all of this
   (download, unzip, enable site-packages, bootstrap pip, install
   requirements) so it's consistent every time and doesn't rely on
   remembering the manual steps.

3. **`launcher.exe`** — built with the command:
   ```
   pyinstaller --onefile --noconsole --icon=src/icon.ico --name=launcher launcher.py
   ```
   This wraps `launcher.py` into a single windowless .exe with an icon
   baked in, so Start Menu / Desktop shortcuts have a proper icon instead
   of a generic one. PyInstaller's output (`dist/launcher.exe`) then needs
   to be copied next to `setup.iss`, since that's where `setup.iss`
   expects to find it.

4. **Inno Setup compile** — `setup.iss` is compiled (via the Inno Setup
   Compiler GUI, or `ISCC.exe setup.iss` from the command line) into
   `LexisApp-Setup.exe`. It packages:
   - `launch.vbs`, `launch.bat` → app root
   - `src/*` → `{app}\app`
   - `python/*` (the embedded runtime + deps) → `{app}\python`
   - `launcher.exe` → app root
   - Start Menu and Desktop shortcuts, both pointing at `launcher.exe`
   - An uninstall step that also deletes `%localappdata%\LexisApp` (where
     downloaded models / user data live), so uninstalling
     doesn't leave that behind

`build/windows/build.ps1` automates steps 2–4 into one script — see the
main README for how to run it.

## Runtime flow (on the end user's machine)

1. **Installer runs** — copies everything above into
   `{Program Files}\LexisApp` (or the per-user equivalent, since
   `PrivilegesRequired=lowest`), and creates the two shortcuts.

2. **User clicks the shortcut** → `launcher.exe` runs → hands off to
   `launch.vbs` → which runs `launch.bat` with a hidden window.

3. **`launch.bat` runs** — starts `pythonw.exe app\serve.py` in the
   background (via `start ""`, so it doesn't block), then polls
   `http://localhost:8000` in a loop using the embedded `python.exe` until
   it responds, then opens the user's default browser to that URL.

4. **`serve.py` runs** — puts `src/` on `sys.path`, starts `tray.py`'s
   tray icon on a background thread (Open / Quit menu), then hands off to
   `textual_serve.Server`, which runs `app.py` as a subprocess and serves
   its terminal UI as a web page on port 8000. This call blocks, keeping
   the whole process alive.

5. **Browser opens** to `localhost:8000`, showing the running Textual app
   (`app.py`), which starts on its "management" screen.

6. **Quitting** — the tray icon's "Quit" option stops the tray icon and
   sends `SIGTERM` to the `serve.py` process.

## Note

- **`PrivilegesRequired=lowest` + `DefaultDirName={autopf}\LexisApp`**:
  `PrivilegesRequired=lowest` means the installer never demands admin
  rights or a UAC prompt. `{autopf}` is an "auto" constant — Inno Setup
  resolves it to the real Program Files if the installer happens to run
  elevated, and quietly falls back to a per-user location under the
  user's own AppData if it doesn't. Together they mean LexisApp installs
  cleanly for a standard, non-admin user, which is the right behavior for
  a single-user desktop/tray app. No change needed — this is documented
  inline in `setup.iss` now.
