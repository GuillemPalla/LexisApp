from src.models.Lexis1 import Lexis1
from src.models.Lexis2 import Lexis2
from src.models.model_config import Lexis1ModelConfig, Lexis2ModelConfig

MODEL_REGISTRY = {
    "Lexis-1": Lexis1,
    "gpt1": Lexis1,
    "Lexis-2": Lexis2
}

CONFIG_REGISTRY = {
    "Lexis-1": Lexis1ModelConfig,
    "gpt1": Lexis1ModelConfig,  # (Which points to Lexis1ModelConfig)
    "Lexis-2": Lexis2ModelConfig
}