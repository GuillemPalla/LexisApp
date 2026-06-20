import json
from safetensors.torch import load_file
import torch
from torch.nn import functional as F

from src.models.registry import CONFIG_REGISTRY, MODEL_REGISTRY
from src.tokenizer.registry import TOKENIZER_REGISTRY


MAX_LENGTH = 100
TEMPERATURE = 0.7
TOP_K = 40
TOP_P = 0.9

class InferenceEngine:
    def __init__(self, model_path: str, tokenizer_name: str):
        config_path = model_path / "config.json"
        with open(config_path, "r") as f:
            model_config = json.load(f)
        
        model_type = model_config["model_type"]

        config_dataclass = CONFIG_REGISTRY[model_type]
        config_object = config_dataclass(**model_config)

        self.model = MODEL_REGISTRY[model_type](config_object)
    
        weights_path = model_path / "model.safetensors"
        state_dict = load_file(str(weights_path))
        
        # Logic to handle the case where the model was saved with tied weights
        if "transformer.wte.weight" not in state_dict and "lm_head.weight" in state_dict:
            # Safely tie them back together in the state dict
            state_dict["transformer.wte.weight"] = state_dict["lm_head.weight"]
        elif "lm_head.weight" not in state_dict and "transformer.wte.weight" in state_dict:
            state_dict["lm_head.weight"] = state_dict["transformer.wte.weight"]

        # Inject the loaded weights into architecture
        # strict=True ensures your architecture matches the weights exactly
        self.model.load_state_dict(state_dict, strict=True)
        
        # Set the model to evaluation mode (turns off dropout, batchnorm, etc.)
        self.model.eval()

        self.tokenizer = TOKENIZER_REGISTRY[tokenizer_name]()

    @torch.no_grad()
    def generate(self, prompt: str = None):
        tokens = self.tokenizer.encode(prompt)
        prompt_len = len(tokens)
        
        xgen = torch.tensor(tokens, dtype=torch.long).unsqueeze(0) # Batch size = 1
        
        while xgen.size(1) < MAX_LENGTH:
            xgen_crop = xgen[:, -self.model.config.block_size:]

            with torch.autocast(device_type=xgen.device.type, dtype=torch.bfloat16):
                logits = self.model(xgen_crop)
            
            logits = logits[:, -1, :] # Last position token
            
            if TEMPERATURE == 0:
                next_token = torch.argmax(logits, dim=-1, keepdim=True)
            else:
                logits = logits / TEMPERATURE
                probs = F.softmax(logits, dim=-1)
                topk_probs, topk_indices = torch.topk(probs, k=TOP_K, dim=-1)
                
                if TOP_P < 1.0:
                    cumulative_probs = torch.cumsum(topk_probs, dim=-1)
                    sorted_indices_to_remove = cumulative_probs - topk_probs > TOP_P
                    topk_probs = topk_probs.masked_fill(sorted_indices_to_remove, 0.0)
                    topk_probs = topk_probs / topk_probs.sum(dim=-1, keepdim=True)
                
                ix = torch.multinomial(topk_probs, num_samples=1)
                next_token = torch.gather(topk_indices, dim=-1, index=ix)
            
            # Check if EOT token is reached
            if next_token.item() == self.tokenizer.eot_token:
                break

            xgen = torch.cat((xgen, next_token), dim=1)

            # Yield the decoded token to the caller for streaming output
            yield self.tokenizer.decode([next_token.item()])