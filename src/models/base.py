from abc import ABC, abstractmethod
import torch.nn as nn

from src.models.model_config import BaseModelConfig


class BaseTransformer(nn.Module, ABC):
    def __init__(self, config):
        super().__init__()
        self.config: BaseModelConfig = config

    @abstractmethod
    def forward(self, idx, targets=None):
        pass