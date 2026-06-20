from dataclasses import dataclass
from typing import Literal

AttnLayersTypes = Literal["global", "local"]

@dataclass
class BaseModelConfig:
    model_type: str

    block_size: int
    vocab_size: int

    n_layer: int
    n_head: int
    n_embd: int

    flash_attention: bool

    # Weight initialization
    wi_std: float
    wi_mean: float

@dataclass
class Lexis1ModelConfig(BaseModelConfig):
    window_size: int
    attn_layers: list[AttnLayersTypes]

@dataclass
class Lexis2ModelConfig(BaseModelConfig):
    rope_base: float
    dropout: float
    n_kv_head: int

#! Initially I had a single ModelConfig class, but as I added more model types, 
#! it became clear that I needed separate config classes for each model type to handle their specific parameters. 
#! Since the first GPT1 checkpoints have ModelConfig in their state dicts, this alias allows to load those checkpoints 
#! without issues.
#! In the future, I can consider refactoring old checkpoints to replace ModelConfig with the appropriate specific config class.
GPT1ModelConfig = Lexis1ModelConfig
ModelConfig = GPT1ModelConfig
GPT2ModelConfig = Lexis2ModelConfig