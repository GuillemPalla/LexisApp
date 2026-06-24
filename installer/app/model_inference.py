import json
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import onnxruntime as ort

from tokenizer.registry import TOKENIZER_REGISTRY


MAX_LENGTH = 1000

@dataclass(frozen=True)
class SamplingPreset:
    label: str
    description: str
    temperature: float
    top_k: int
    top_p: float

    def params_summary(self) -> str:
        return f"temp {self.temperature:g} · top-k {self.top_k} · top-p {self.top_p:g}"


SAMPLING_PRESETS: dict[str, SamplingPreset] = {
    "deterministic": SamplingPreset(
        "Deterministic",
        "Always picks the most likely next token — same prompt, same output every time.",
        0.0,
        1,
        1.0,
    ),
    "instruction-following": SamplingPreset(
        "Instruction-following",
        "Low randomness for steady, predictable continuations that stay close to your prompt.",
        0.3,
        20,
        0.85,
    ),
    "standard": SamplingPreset(
        "Standard",
        "Balanced creativity and coherence — a good default for general text completion.",
        0.7,
        40,
        0.9,
    ),
    "creative": SamplingPreset(
        "Creative",
        "More varied word choices and less predictable continuations.",
        1.0,
        60,
        0.95,
    ),
    "experimental": SamplingPreset(
        "Experimental",
        "Maximum randomness — output may diverge sharply from the prompt.",
        1.5,
        100,
        0.99,
    ),
}

PRESET_ORDER = list(SAMPLING_PRESETS.keys())
DEFAULT_PRESET_KEY = "standard"

class InferenceEngine:
    def __init__(self, model_path: str, tokenizer_name: str):
        model_dir = Path(model_path)
        
        # Read block size out of config file
        config_path = model_dir / "config.json"
        with open(config_path, "r") as f:
            model_config = json.load(f)
        self.block_size = model_config.get("block_size", 1024)
        
        onnx_file_path = model_dir / "model.onnx"
        print(f"Initializing DirectML ONNX Session for {onnx_file_path}...")
        
        # Create an object to customize how the ONNX engine executes our model graph
        options = ort.SessionOptions()
        
        # CRITICAL FOR DIRECTML: Disable ONNX's native CPU-optimized memory manager. 
        # This prevents ONNX Runtime from fighting with your Windows GPU drivers (DirectX 12) over VRAM control.
        options.enable_mem_pattern = False
        
        # Forces operators/layers to execute one after the other. This prevents multi-threading 
        # race conditions across unpredictable client graphics cards (NVIDIA, AMD, Intel).
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        # Define execution priority: try DirectML (Windows GPU) first; if it's missing, safely drop back to the CPU.
        providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
        
        # Instantiate the actual binary runner session, passing the model path, our configuration options, and hardware drivers.
        self.ort_session = ort.InferenceSession(str(onnx_file_path), sess_options=options, providers=providers)
        
        # Look inside the compiled ONNX graph and automatically find the name of its first input node (e.g., "input_ids").
        # This saves us from having to hardcode what the PyTorch exporter named it.
        self.input_name = self.ort_session.get_inputs()[0].name
        
        # Load tokenizer
        self.tokenizer = TOKENIZER_REGISTRY[tokenizer_name]()
        
        self._sampling_key = DEFAULT_PRESET_KEY
        
    @property
    def sampling_preset_key(self) -> str:
        return self._sampling_key

    def set_sampling_preset(self, key: str) -> None:
        if key not in SAMPLING_PRESETS:
            raise ValueError(f"Unknown sampling preset: {key!r}")
        self._sampling_key = key

    def generate(self, prompt: str = None):
        # Convert raw text string into a 1D sequence of numerical token IDs
        tokens = self.tokenizer.encode(prompt)
        
        # Keep sequence tracking inside a light Python native list.
        # Python lists are heavily optimized for single-item appends (O(1)), making them 
        # much lighter and faster for text loops than repeatedly resizing a PyTorch or NumPy tensor.
        xgen = list(tokens)
        
        while len(xgen) < MAX_LENGTH:
            # Enforce the context window limit. If our text sequence gets too long, 
            # slice off the oldest tokens so we don't violate the model's structural block size limit.
            xgen_crop = xgen[-self.block_size:]

            # Wrap our 1D list into a structured 2D NumPy Array.
            # ONNX strictly expects dimensions matching: (batch_size, sequence_length).
            # Writing [xgen_crop] adds that necessary outer batch dimension of 1.
            input_numpy = np.array([xgen_crop], dtype=np.int64)
            
            # Run the data forward through the ONNX graph on the system GPU via DirectML.
            # It returns a list containing all outputs. We grab the first element ([0]), which holds the logits.
            ort_outputs = self.ort_session.run(None, {self.input_name: input_numpy})
            logits_raw = ort_outputs[0]  # Shape: (batch_size=1, sequence_length, vocabulary_size)
            
            # Isolate token predictions for the final sequence character index.
            # We index 0 (the only batch) and -1 (the absolute last generated token) to isolate a 1D array of vocabulary scores.
            logits = logits_raw[0, -1, :]
            
            # Fetch user configuration values based on the current active preset
            temperature = SAMPLING_PRESETS[self._sampling_key].temperature
            top_k = SAMPLING_PRESETS[self._sampling_key].top_k
            top_p = SAMPLING_PRESETS[self._sampling_key].top_p

            # Greedy Search: No randomness. Find the index with the absolute highest raw score.
            if temperature == 0:
                next_token = int(np.argmax(logits))
            else:
                # Scale raw model confidence scores by temperature before calculating probabilities.
                logits = logits / temperature
                
                # Sort vocabulary array indices from highest score to lowest score.
                # np.argsort sorts ascending; adding [::-1] flips it to descending order.
                sorted_indices = np.argsort(logits)[::-1]
                sorted_logits = logits[sorted_indices]
                
                # --- TOP-K FILTERING STEP ---
                # Truncate our sorted search space. Discard all words outside the top 'K' slots.
                if top_k > 0 and top_k < len(sorted_logits):
                    sorted_logits = sorted_logits[:top_k]
                    sorted_indices = sorted_indices[:top_k]
                
                # --- MANUAL SOFTMAX CALCULATION ---
                # Convert raw arbitrary logits into strict 0.0 to 1.0 percentage probabilities.
                # Subtracting 'np.max(sorted_logits)' is a standard safety trick that prevents exponential overflow crashes.
                probs = np.exp(sorted_logits - np.max(sorted_logits))
                probs /= np.sum(probs)  # Ensure everything sums up cleanly to exactly 1.0
                
                # --- TOP-P (NUCLEUS) FILTERING STEP ---
                # Keep accumulating sorted word choices until their combined probability hits our threshold (e.g., 90%).
                if top_p < 1.0:
                    cumulative_probs = np.cumsum(probs) # Create running total sum array
                    
                    # Find indices where the cumulative total hasn't crossed the boundary yet
                    keep_idx = np.where(cumulative_probs <= top_p)[0]
                    
                    if len(keep_idx) == 0:
                        # If the very first word was already higher than top_p, preserve at least that single choice
                        keep_idx = [0]
                    else:
                        # Include the very first token that crossed the line so our choice pool isn't empty or truncated too early
                        last_idx = keep_idx[-1]
                        if last_idx + 1 < len(probs):
                            keep_idx = np.append(keep_idx, last_idx + 1)
                    
                    # Cut down our options and re-normalize probabilities so they sum to 1.0 again
                    probs = probs[keep_idx]
                    probs /= np.sum(probs)  
                    sorted_indices = sorted_indices[keep_idx]
                
                # --- STOCHASTIC SAMPLING PASS ---
                # Roll a random number matching our finalized probability weights to select the next word ID.
                next_token = int(np.random.choice(sorted_indices, p=probs))
            
            # If the model emits its special End-Of-Text token, break out of the loop and stop generating text.
            if next_token == self.tokenizer.eot_token:
                break

            # Append the newly verified token directly to our historical tracker list
            xgen.append(next_token)
            
            # Yield the single string word to the calling application layout in real-time (streaming text)
            yield self.tokenizer.decode([next_token])