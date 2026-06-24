# LexisApp

.\clean_env\Scripts\Activate.ps1
pip freeze > requirements.txt

pyinstaller --clean --console --name lexis_tui --collect-all textual --collect-all onnxruntime --add-data "tokenizer;tokenizer" --hidden-import _overlapped --hidden-import asyncio --hidden-import asyncio.windows_events --hidden-import asyncio.windows_utils --hidden-import encodings --hidden-import encodings.utf_8 --hidden-import encodings.cp65001 app.py

pyinstaller --clean --windowed --name Lexis --add-data "alacritty.exe;." --add-data "alacritty.toml;." launcher.py

copy alacritty.exe dist\Lexis\alacritty.exe
copy alacritty.toml dist\Lexis\alacritty.toml
copy dist\lexis_tui\lexis_tui.exe dist\Lexis\lexis_tui.exe


Key Flags Explained:
--clean: Clears the PyInstaller cache before building (prevents old dependency remnants).

--console: Crucial for Textual. Do not use --windowed or -w. Textual apps run inside a terminal; hiding the console will cause the app to crash instantly on launch.

--collect-all onnxruntime: Forces PyInstaller to grab all binaries (DirectML.dll, onnxruntime_providers_shared.dll, etc.) and metadata for ONNX.

--collect-all textual: Ensures Textual's internal assets and dependencies (like rich) are bundled flawlessly.

Note on --onefile vs --onedir: By default, the command above creates a --onedir (a folder containing an .exe and dozens of files). While you can use --onefile to get a single executable, onnxruntime and textual will take several seconds to unpack to a temporary directory every single time the user launches the app. For a smooth user experience, --onedir combined with an installer is highly recommended.