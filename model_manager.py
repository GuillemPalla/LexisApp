from pathlib import Path
from platformdirs import user_data_dir
from huggingface_hub import hf_hub_download

# Setup standard user data directory for your app
APP_NAME = "LexisLocalLLM"
DATA_DIR = Path(user_data_dir(APP_NAME))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Example map of friendly names to your HF repos/files
AVAILABLE_MODELS = {
    "Mini-LLM 100M": {"repo_id": "your-username/mini-llm-100m", "filename": "weights.pt"},
    "Tiny-LLM 300M": {"repo_id": "your-username/tiny-llm-300m", "filename": "weights.pt"},
}

def get_local_model_path(model_name: str) -> Path:
    """Returns the local path where the model should exist."""
    model_info = AVAILABLE_MODELS[model_name]
    return DATA_DIR / model_info["repo_id"].split("/")[-1] / model_info["filename"]

def is_model_downloaded(model_name: str) -> bool:
    """Checks if the model weights already exist locally."""
    return get_local_model_path(model_name).exists()

def download_model_weights(model_name: str, progress_callback=None) -> Path:
    """Downloads weights from HF. 
    Note: For a production Textual app, you'd hook the callback into a Textual ProgressBar.
    """
    model_info = AVAILABLE_MODELS[model_name]
    target_path = get_local_model_path(model_name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Download file via HF Hub
    # downloaded_path = hf_hub_download(
    #     repo_id=model_info["repo_id"],
    #     filename=model_info["filename"],
    #     local_dir=target_path.parent
    # )
    # return Path(downloaded_path)
    return ''