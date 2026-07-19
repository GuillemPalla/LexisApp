# LexisApp

A Textual app for downloading and running small ONNX language models
locally, packaged as a Windows desktop app: install it, and it runs
quietly in the system tray while serving its UI to your browser on
`http://localhost:8000`.

Developed for PFG GEINF.

The visual components of this application (/src/screens) were generated with the assistance of AI using Cursor IDE, with minimal human intervention.

The build pipeline (/build/windows), due to its complexity, was also developed with AI assistance, but involved significantly more human intervention, analysis, and refinement. See BUILD.md for more details.

## Project layout

```
LexisApp/
├── src/                  # the app — single source of truth, dev and prod
│   ├── app.py             # entry point (Textual App)
│   ├── serve.py           # desktop wrapper: tray icon + textual-serve on :8000
│   ├── tray.py             # system tray icon (Open / Quit)
│   ├── icon.ico
│   ├── screens/
│   └── tokenizers/
├── requirements.txt
├── build/
    └── windows/           # Windows-installer packaging, nothing else
       ├── setup.iss        # Inno Setup script
       ├── launch.bat       # polls :8000, opens the browser once it's up
       ├── launch.vbs       # runs launch.bat with a hidden window
       ├── launcher.py      # compiled to launcher.exe (Start Menu / Desktop icon)
       └── build.ps1        # builds the whole installer in one command

```

## Development

```bash
# Create venv
python -m venv .venv
# activate
source .venv/bin/activate # macOS/Linux
.venv\Scripts\activate # Windows

pip install -r requirements.txt
cd src
python app.py
```

## Building the Windows installer

See [`docs/BUILD.md`](docs/BUILD.md) for the full write-up. Short version,
from a Windows machine with PyInstaller and Inno Setup 6 installed:

```powershell
cd build\windows
.\build.ps1
```

This produces `build\windows\Output\LexisApp-Setup.exe`.
