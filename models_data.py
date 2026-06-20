HF_USERNAME = "GuillemPallares"

# Dataset categories: define display name + description shown in the model list
DATASET_CATEGORIES = {
    "tiny_stories": {
        "label": "TinyStories",
        "short_description": "Short, simple stories for kids.",
        "description": (
            "Models trained on short, simple English stories. "
            "Expect fluent narrative generation with a gentle, story-like tone — "
            "well-suited for creative writing assistance and text completion tasks."
        ),
    },
    "only_sports": {
        "label": "OnlySports",
        "short_description": "Athletic commentary and match reports.",
        "description": (
            "Models fine-tuned on sports commentary, match reports, and athletic content. "
            "Optimised for sports Q&A, live commentary style, and domain-specific language "
            "around scores, teams, and competitions."
        ),
    },
}

AVAILABLE_MODELS = {
    "Lexis1-TS-1M": {
        "title": "Lexis 1 — TinyStories 1M",
        "description": "A compact 1M-parameter model fine-tuned on the TinyStories dataset. Generates coherent short narratives with simple vocabulary.",
        "parameters": "1 Million",
        "architecture": "Transformer Decoder (Grouped-Query Attention, RoPE, SiLU)",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-1M",
        "tokenizer": "tiny_stories_unk",
        "category": "tiny_stories",
    },
    "Lexis2-OS-110M": {
        "title": "Lexis 2 — OnlySports 110M",
        "description": "A 110M-parameter model fine-tuned exclusively on sports content. Produces sports-domain text with accurate terminology and commentary style.",
        "parameters": "110 Million",
        "architecture": "Transformer Decoder (Grouped-Query Attention, RoPE, SiLU)",
        "repo_id": f"{HF_USERNAME}/Lexis2-OS-110M",
        "tokenizer": "onlysports",
        "category": "only_sports",
    },
}