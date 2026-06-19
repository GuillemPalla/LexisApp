import json
from safetensors.torch import load_file
import torch

from models.registry import MODEL_REGISTRY

NUM_RETURN_SEQUENCES = 1
MAX_LENGTH = 1000

TEMPERATURE = 0.7
TOP_K = 40
TOP_P = 0.9

class InferenceEngine:
    def __init__(self, model_path: str):
        config_path = model_path / "config.json"
        with open(config_path, "r") as f:
            model_config = json.load(f)
        
        self.model = MODEL_REGISTRY[model_config["model_type"]](model_config)
        
        weights_path = model_path / "model.safetensors"
        print(f"Loading weights from {weights_path.name}...")
        state_dict = load_file(str(weights_path))
        
        # Inject the loaded weights into architecture
        # strict=True ensures your architecture matches the weights exactly
        self.model.load_state_dict(state_dict, strict=True)
        
        # Set the model to evaluation mode (turns off dropout, batchnorm, etc.)
        self.model.eval()

    @torch.no_grad()
    def generate(self, prompt: str = None):
        tokens = None
        if prompt:
            tokens = tokenizer.encode(prompt)
            tokens = torch.tensor(tokens, dtype=torch.long)
            xgen = tokens.unsqueeze(0).repeat(NUM_RETURN_SEQUENCES, 1)
        else:
            xgen = torch.zeros((NUM_RETURN_SEQUENCES,1), dtype=torch.long)
        
        # Track which sequences in the batch have finished
        is_finished = torch.zeros(NUM_RETURN_SEQUENCES, dtype=torch.bool)
        
        while xgen.size(1) < MAX_LENGTH:
            # Crop context window to the model's maximum allowed block size
            # If xgen length is less than block_size, this safely returns the whole tensor.
            xgen_crop = xgen[:, -self.model.config.block_size:]

            with torch.autocast(dtype=torch.bfloat16):
                logits, _ = self.model(xgen_crop) # (num_return_sequences, T, vocab_size)
            # take the logits at the last position
            logits = logits[:, -1, :] # (num_return_sequences, vocab_size)
            if TEMPERATURE == 0:
                # Greedy decoding (deterministic)
                next_token = torch.argmax(logits, dim=-1, keepdim=True)
            else:
                logits = logits / TEMPERATURE
                # get the probabilities
                probs = F.softmax(logits, dim=-1) # (num_return_sequences, vocab_size)
                # do top-k sampling of 50
                topk_probs, topk_indices = torch.topk(probs, k=TOP_K, dim=-1) # (num_return_sequences, k)
                # apply top-p (nucleus) filtering: keep the smallest set of tokens whose cumulative prob >= TOP_P
                if TOP_P < 1.0:
                    cumulative_probs = torch.cumsum(topk_probs, dim=-1)
                    # remove tokens once cumulative probability exceeds TOP_P (shift right to keep at least one token)
                    sorted_indices_to_remove = cumulative_probs - topk_probs > TOP_P
                    topk_probs = topk_probs.masked_fill(sorted_indices_to_remove, 0.0)
                    topk_probs = topk_probs / topk_probs.sum(dim=-1, keepdim=True)  # renormalize
                # select a token from the top-k probabilities
                ix = torch.multinomial(topk_probs, num_samples=1) # (num_return_sequences, 1)
                # torch.gather is used to select the next token IDs from the topk_indices tensor based on the sampled indices in ix.
                next_token = torch.gather(topk_indices, dim=-1, index=ix) # (num_return_sequences, 1)
            
            # Update which sequences have hit EOT
            is_finished |= (next_token.squeeze(-1) == eot_token)

            xgen = torch.cat((xgen, next_token), dim=1) # append to the sequence

            # Stop if EVERY sequence in the batch has generated an EOT token
            if is_finished.all():
                break

        for i in range(NUM_RETURN_SEQUENCES):
            tokens = xgen[i].tolist()
            # Truncate each list at the EOT token
            if eot_token in tokens:
                tokens = tokens[:tokens.index(eot_token)]
            decoded = tokenizer.decode(tokens)
            print(f"--- Sequence {i+1} ---\n{decoded}\n")