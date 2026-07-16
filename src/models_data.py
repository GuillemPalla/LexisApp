HF_USERNAME = "GuillemPallares"

DATASET_CATEGORIES = {
    "tiny_stories": {
        "label": "TinyStories",
        "short_description": "Synthetic short stories with simple vocabulary.",
        "description": (
            "Models trained on the TinyStories Dataset — "
            "GPT-3.5 and GPT-4 generated English stories constrained to a small vocabulary. "
            "Expect clear, child-friendly narrative with simple words and a gentle story-like tone."
        ),
    },
    "only_sports": {
        "label": "OnlySports",
        "short_description": "Sports news, reports, and commentary from the web.",
        "description": (
            "Models trained on the OnlySports Dataset — "
            "a large English sports corpus filtered from FineWeb using URL keywords and a dedicated classifier. "
            "Covers news, blogs, match reports, interviews, and tutorials across leagues and sports "
            "(2017-2024). "
            "Strong at sports terminology, commentary style, and domain Q&A around teams, scores, and competitions."
        ),
    },
    "python": {
        "label": "Python",
        "short_description": "Educational Python code from open-source repos.",
        "description": (
            "Models trained on the python-edu-cleaned Dataset — "
            "a curated subset of SmolLM-Corpus Python-Edu: real Python files from The Stack v2 "
            "scored for educational quality, with low-quality artefacts removed. "
            "Suited to code completion, explanations, and programming tasks in idiomatic Python."
        ),
    },
}

TOKENIZERS = {
    "tiny_stories_unk": {
        "label": "TinyStories",
        "vocab_size": 10_000,
    },
    "onlysports": {
        "label": "OnlySports",
        "vocab_size": 32_000,
    },
    "python_edu": {
        "label": "Python-edu",
        "vocab_size": 32_000,
    },
}

ARCHITECTURES = {
    "Lexis 1": {
        "features": [
            "Sliding Window Attention (SWA)",
            "Alternating Local / Global Layers",
            "Learnable Positional Embeddings Matrix",
        ],
        "details": {
            "Sliding Window Attention (SWA)": (
                "Each local layer attends only to a fixed neighbourhood of tokens "
                "instead of the full sequence. This keeps the "
                "attention cost linear in the window rather than quadratic in sequence length."
            ),
            "Alternating Local / Global Layers": (
                "Layers alternate: odd-indexed layers use the local SWA window, "
                "even-indexed layers attend to the full context. This lets the model capture "
                "both fine-grained local patterns and long-range dependencies cheaply."
            ),
            "Learnable Positional Embeddings Matrix": (
                "Position is encoded via a learned embedding matrix added to token "
                "embeddings at each index. The model learns position-specific "
                "representations directly from data rather than using fixed or rotary encodings."
            ),
        },
    },

    "Lexis 2": {
        "features": [
            "Grouped-Query Attention (GQA)",
            "RoPE",
            "SwiGLU",
            "RMSNorm",
        ],
        "details": {
            "Grouped-Query Attention (GQA)": (
                "GQA shares key/value heads across groups of query heads. This cuts the KV-cache memory by 3× versus "
                "Multi-Head Attention while preserving most of the modelling quality."
            ),
            "RoPE": (
                "Rotary Position Embeddings encode position directly into the query/key "
                "dot-product via rotation matrices, allowing the model to extrapolate "
                "to sequence lengths beyond those seen during training."
            ),
            "SwiGLU": (
                "Swish-Gated Linear Unit activation used in the feed-forward block. "
                "Empirically outperforms ReLU and GELU on language modelling tasks "
                "while adding negligible parameter overhead."
            ),
            "RMSNorm": (
                "Root-Mean-Square Layer Normalisation — a simpler, faster alternative "
                "to LayerNorm that omits the mean-centering step without loss of "
                "training stability."
            ),
        },
    },
}

AVAILABLE_MODELS = {
    "Lexis1-TS-1M": {
        "title": "Lexis 1 · TinyStories Micro",
        "description": (
            "A compact 1M-parameter model fine-tuned on the TinyStories dataset. "
            "Generates coherent short narratives with simple vocabulary. "
            "Designed to explore efficient attention patterns at tiny scale."
        ),
        "parameters": "1.07 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-1M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 8,
        "attention_heads": 16,
        "embedding_dim": 64,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 1",

        # SWA-specific extras (Lexis 1 only)
        "swa_window_size": 256,
        "swa_pattern": "Odd layers: local (w=256) · Even layers: global (full context)",
    },

    "Lexis1-TS-3M": {
        "title": "Lexis 1 · TinyStories Mini",
        "description": (
            "A ~3M-parameter Lexis 1 model with wider embeddings than the 1M variant. "
            "Produces clearer short stories while keeping the same alternating local/global SWA stack. "
            "A practical step up in expressiveness without leaving the tiny-model regime."
        ),
        "parameters": "2.94 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-3M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 8,
        "attention_heads": 16,
        "embedding_dim": 128,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 1",

        # SWA-specific extras (Lexis 1 only)
        "swa_window_size": 256,
        "swa_pattern": "Odd layers: local (w=256) · Even layers: global (full context)",
    },

    "Lexis1-TS-8M": {
        "title": "Lexis 1 · TinyStories Small",
        "description": (
            "A ~9M-parameter Lexis 1 model that doubles embedding width to 256. "
            "Balances narrative quality and efficiency on TinyStories with 8 SWA layers. "
            "Suited to experiments where sub-10M models need noticeably richer language."
        ),
        "parameters": "9.01 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-8M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 8,
        "attention_heads": 16,
        "embedding_dim": 256,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 1",

        # SWA-specific extras (Lexis 1 only)
        "swa_window_size": 256,
        "swa_pattern": "Odd layers: local (w=256) · Even layers: global (full context)",
    },

    "Lexis1-TS-28M": {
        "title": "Lexis 1 · TinyStories Large",
        "description": (
            "The deep Lexis 1 flagship at ~31M parameters with 512-dim embeddings across 8 layers. "
            "Delivers the strongest story coherence in the Lexis 1 TinyStories line while retaining "
            "efficient sliding-window attention."
        ),
        "parameters": "30.61 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-28M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 8,
        "attention_heads": 16,
        "embedding_dim": 512,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 1",

        # SWA-specific extras (Lexis 1 only)
        "swa_window_size": 256,
        "swa_pattern": "Odd layers: local (w=256) · Even layers: global (full context)",
    },

    "Lexis1-TS-33M": {
        "title": "Lexis 1 · TinyStories Large Wide",
        "description": (
            "A ~36M-parameter Lexis 1 variant that trades depth for width — 4 layers with 768-dim embeddings. "
            "Explores whether a shallow, wide SWA stack can match deeper models on simple narratives. "
            "Same TinyStories training budget with a distinct capacity profile."
        ),
        "parameters": "36.45 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-33M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 4,
        "attention_heads": 16,
        "embedding_dim": 768,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 1",

        # SWA-specific extras (Lexis 1 only)
        "swa_window_size": 256,
        "swa_pattern": "Odd layers: local (w=256) · Even layers: global (full context)",
    },

    "Lexis2-TS-28M": {
        "title": "Lexis 2 · TinyStories Large",
        "description": (
            "A ~32M-parameter Lexis 2 model trained on TinyStories — a modern counterpart to Lexis1-TS-28M. "
            "Uses GQA, RoPE, SwiGLU, and RMSNorm across 8 layers with 512-dim embeddings. "
            "Lets you compare next-generation architecture against Lexis 1 at similar scale."
        ),
        "parameters": "29.27 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis2-TS-28M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 8,
        "attention_heads": 16,
        "kv_heads": 4,
        "embedding_dim": 512,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 2",
    },

    "Lexis2-TS-110M": {
        "title": "Lexis 2 · TinyStories Max",
        "description": (
            "The largest TinyStories model in the catalog at ~93M parameters and 12 layers. "
            "Combines Lexis 2's full modern stack with 768-dim embeddings for the best narrative "
            "quality on simple-vocabulary stories."
        ),
        "parameters": "83.23 Million",
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis2-TS-110M",
        "tokenizer": "tiny_stories_unk",

        # Specs
        "context_size": 512,
        "layers": 12,
        "attention_heads": 12,
        "kv_heads": 4,
        "embedding_dim": 768,
        "tokens_trained": "4.69 Billion",

        # Architecture
        "arch_family": "Lexis 2",
    },

    "Lexis2-OS-110M": {
        "title": "Lexis 2 · OnlySports Max",
        "description": (
            "A 110M-parameter model fine-tuned exclusively on sports content. "
            "Produces sports-domain text with accurate terminology and commentary style. "
            "Uses Grouped-Query Attention for a favourable quality-to-cost trade-off."
        ),
        "parameters": "106.85 Million",
        "category": "only_sports",
        "repo_id": f"{HF_USERNAME}/Lexis2-OS-110M",
        "tokenizer": "onlysports",

        # Specs
        "context_size": 1024,
        "layers": 30,
        "attention_heads": 16,
        "kv_heads": 4,
        "embedding_dim": 512,
        "tokens_trained": "4.3 Billion",

        # Architecture
        "arch_family": "Lexis 2",
    },

    "Lexis2-OS-110M-512CS": {
        "title": "Lexis 2 · OnlySports Max Turbo",
        "description": (
            "The same ~110M-parameter Lexis 2 OnlySports model with a 512-token context window. "
            "Covers sports news, commentary, and terminology with lower memory use and faster inference "
            "than the 1024-context variant. GQA keeps KV-cache costs manageable at 30 layers."
        ),
        "parameters": "106.85 Million",
        "category": "only_sports",
        "repo_id": f"{HF_USERNAME}/Lexis2-OS-110M-512CS",
        "tokenizer": "onlysports",

        # Specs
        "context_size": 512,
        "layers": 30,
        "attention_heads": 16,
        "kv_heads": 4,
        "embedding_dim": 512,
        "tokens_trained": "4.3 Billion",

        # Architecture
        "arch_family": "Lexis 2",
    },

    "Lexis2-PY-110M": {
        "title": "Lexis 2 · Python Max",
        "description": (
            "A 110M-parameter model fine-tuned on educational Python code. "
            "Generates idiomatic Python, explains code, and completes programming tasks. "
            "Uses Grouped-Query Attention for a favourable quality-to-cost trade-off."
        ),
        "parameters": "106.85 Million",
        "category": "python",
        "repo_id": f"{HF_USERNAME}/Lexis2-PY-110M",
        "tokenizer": "python_edu",

        # Specs
        "context_size": 1024,
        "layers": 30,
        "attention_heads": 16,
        "kv_heads": 4,
        "embedding_dim": 512,
        "tokens_trained": "4.3 Billion",

        # Architecture
        "arch_family": "Lexis 2",
    },

    "Lexis2-PY-110M-512CS": {
        "title": "Lexis 2 · Python Max Turbo",
        "description": (
            "The same ~110M-parameter Lexis 2 Python model with a 512-token context window. "
            "Covers Python programming concepts, syntax, and best practices with lower memory use and faster inference "
            "than the 1024-context variant. GQA keeps KV-cache costs manageable at 30 layers."
        ),
        "parameters": "106.85 Million",
        "category": "python",
        "repo_id": f"{HF_USERNAME}/Lexis2-PY-110M-512CS",
        "tokenizer": "python_edu",

        # Specs
        "context_size": 512,
        "layers": 30,
        "attention_heads": 16,
        "kv_heads": 4,
        "embedding_dim": 512,
        "tokens_trained": "4.3 Billion",

        # Architecture
        "arch_family": "Lexis 2",
    },
}