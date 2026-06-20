HF_USERNAME = "GuillemPallares"

AVAILABLE_MODELS = {
    "Lexis1-TS-1M": {
        "title": "Llama 3 8B Instruct",
        "description": "Meta's highly optimized 8-billion parameter instruction-tuned generative model, built for dialogue use cases.",
        "parameters": "8.03 Billion",
        "architecture": "Transformer Decoder (Grouped-Query Attention, RoPE, Silu)",
        "size_mb": 4850,
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-1M",
        "tokenizer": "tiny_stories_unk"
    },
    "Lexis2-OS-110M": {
        "title": "Llama 3 8B Open-Source",
        "description": "Meta's highly optimized 8-billion parameter open-source generative model, built for general-purpose use cases.",
        "parameters": "8.03 Billion",
        "architecture": "Transformer Decoder (Grouped-Query Attention, RoPE, Silu)",
        "size_mb": 4850,
        "repo_id": f"{HF_USERNAME}/Lexis2-OS-110M",
        "tokenizer": "onlysports"
    },
}