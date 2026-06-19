import shutil
from pathlib import Path
from platformdirs import user_data_dir
from huggingface_hub import list_repo_files, hf_hub_download
from tqdm import tqdm

APP_NAME = "LexisApp"
DATA_DIR = Path(user_data_dir(APP_NAME))
DATA_DIR.mkdir(parents=True, exist_ok=True)

HF_USERNAME = "GuillemPallares"

AVAILABLE_MODELS = {
    "Lexis1-TS-1M": {"repo_id": f"{HF_USERNAME}/Lexis1-TS-1M"},
    "Lexis2-OS-110M": {"repo_id": f"{HF_USERNAME}/Lexis2-OS-110M"},
}

IGNORE_PATTERNS = {"*.md", ".gitattributes", "README.md"}

def _make_tqdm_class(progress_callback, filename: str) -> type:
    """
    Returns a tqdm subclass that calls progress_callback on every update
    so the UI can refresh.
    """
    class UIPostTqdm(tqdm):
        def update(self, n=1):
            displayed = super().update(n)
            if progress_callback:
                progress_callback(self.n, self.total or 0, filename)
            return displayed

    return UIPostTqdm


def _should_ignore(filename: str) -> bool:
    import fnmatch
    return any(fnmatch.fnmatch(filename, pat) for pat in IGNORE_PATTERNS)


def get_local_model_dir(model_name: str) -> Path:
    """Returns the local directory for the model."""
    model_info = AVAILABLE_MODELS[model_name]
    return DATA_DIR / model_info["repo_id"].split("/")[-1]


def is_model_downloaded(model_name: str) -> bool:
    """Checks if both the weights and config exist locally."""
    model_dir = get_local_model_dir(model_name)
    return (model_dir / "model.safetensors").exists() and (model_dir / "config.json").exists()


def download_model(model_name: str, progress_callback=None) -> Path:
    """
    Downloads all required files for a given model from Hugging Face Hub.
    """
    if progress_callback is None:
        progress_callback = lambda *_: None

    model_info = AVAILABLE_MODELS[model_name]
    repo_id = model_info["repo_id"]
    target_dir = get_local_model_dir(model_name)
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        all_files = [
            f for f in list_repo_files(repo_id)
            if not _should_ignore(f)
        ]

        for filename in all_files:
            tqdm_cls = _make_tqdm_class(progress_callback, filename)

            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=target_dir,
                tqdm_class=tqdm_cls,
            )

    except Exception as e:
        # clean up if it fails due to network or unexpected error
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise e

    return target_dir


def return_model_path(model_name: str) -> Path:
    """Returns the path to the model directory."""
    if not is_model_downloaded(model_name):
        raise FileNotFoundError("Model not downloaded yet.")
    return get_local_model_dir(model_name)