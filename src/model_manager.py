import shutil
import fnmatch
from pathlib import Path
from platformdirs import user_data_dir
from huggingface_hub import list_repo_files, hf_hub_download, repo_info
from tqdm import tqdm

from models_data import AVAILABLE_MODELS

APP_NAME = "LexisApp"
DATA_DIR = Path(user_data_dir(APP_NAME))
DATA_DIR.mkdir(parents=True, exist_ok=True)

IGNORE_PATTERNS = {"*.md", ".gitattributes", "README.md"}
MARKER_FILE = ".download_complete"

# THIS UI FUNCTION HAS BEEN DEVELOPED WITH THE HELP OF AI
def _make_tqdm_class(progress_callback, filename: str) -> type:
    """
    Returns a tqdm subclass that calls progress_callback on every update.
    """
    class UIPostTqdm(tqdm):
        def update(self, n=1):
            displayed = super().update(n)
            if progress_callback:
                # Ensure values don't break if total is missing
                progress_callback(self.n, self.total or 0, filename)
            return displayed

    return UIPostTqdm


def _should_ignore(filename: str) -> bool:
    return any(fnmatch.fnmatch(filename, pat) for pat in IGNORE_PATTERNS)


def get_local_model_dir(model_name: str) -> Path:
    """Returns the local directory for the model."""
    model_info = AVAILABLE_MODELS[model_name]
    return DATA_DIR / model_info["repo_id"].split("/")[-1]


def is_model_downloaded(model_name: str) -> bool:
    """Checks if the local model folder contains our success marker."""
    model_dir = get_local_model_dir(model_name)
    return (model_dir / MARKER_FILE).exists()


# THIS FUNCTION HAS BEEN DEVELOPED WITH THE HELP OF AI
def download_model(model_name: str, progress_callback=None) -> Path:
    """
    Downloads all required files for a given model from Hugging Face Hub.
    Supports native chunk resumption on network failure.
    """
    if progress_callback is None:
        progress_callback = lambda *_: None

    model_info = AVAILABLE_MODELS[model_name]
    repo_id = model_info["repo_id"]
    target_dir = get_local_model_dir(model_name)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Remove completion marker if a re-download/repair is explicitly triggered
    marker = target_dir / MARKER_FILE
    if marker.exists():
        marker.unlink()

    all_files = [
        f for f in list_repo_files(repo_id)
        if not _should_ignore(f)
    ]

    for filename in all_files:
        tqdm_cls = _make_tqdm_class(progress_callback, filename)

        # local_dir_use_symlinks="auto" ensures files are written directly 
        # as actual binaries into your AppData folder, crucial for PyInstaller portability.
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=target_dir,
            local_dir_use_symlinks="auto",
            tqdm_class=tqdm_cls,
        )

    # Place the success marker only when ALL files complete flawlessly
    marker.touch()
    return target_dir


def delete_model(model_name: str) -> None:
    """Deletes the local model directory from disk completely."""
    model_dir = get_local_model_dir(model_name)
    if model_dir.exists():
        shutil.rmtree(model_dir, ignore_errors=True)


def return_model_path(model_name: str) -> Path:
    """Returns the path to the model directory."""
    if not is_model_downloaded(model_name):
        raise FileNotFoundError(f"Model '{model_name}' is not fully downloaded yet.")
    return get_local_model_dir(model_name)


def return_model_tokenizer(model_name: str) -> str:
    """Returns the tokenizer identifier for the model."""
    return AVAILABLE_MODELS[model_name]["tokenizer"]


# Model size caching
_size_cache: dict[str, float] = {}

def get_cached_model_size_mb(model_name: str) -> float | None:
    return _size_cache.get(model_name)

def prefetch_model_sizes(model_names: list[str] | None = None) -> None:
    for name in model_names or AVAILABLE_MODELS:
        try:
            get_model_size_mb(name)
        except Exception:
            pass

def get_model_size_mb(model_name: str) -> float:
    if model_name in _size_cache:
        return _size_cache[model_name]
    
    model_info = AVAILABLE_MODELS[model_name]
    repo_id = model_info["repo_id"]
    info = repo_info(repo_id, repo_type="model", files_metadata=True)

    total_bytes = sum(
        s.size for s in (info.siblings or [])
        if s.size and not _should_ignore(s.rfilename)
    )

    size_mb = round(total_bytes / (1024 * 1024), 1)
    _size_cache[model_name] = size_mb
    return size_mb