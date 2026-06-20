HF_USERNAME = "GuillemPallares"

# ── Dataset categories ────────────────────────────────────────────────────────
# Define display name + description shown in the model list.

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


# ── Architecture definitions ──────────────────────────────────────────────────
# Each architecture family owns its feature list and per-feature explanations.
# Models reference a family by name; no duplication across model entries.

ARCHITECTURES = {
    "Lexis 1": {
        "features": [
            "Sliding Window Attention (SWA)",
            "Alternating Local / Global Layers",
            "RoPE",
            "SwiGLU",
            "RMSNorm",
        ],
        "details": {
            "Sliding Window Attention (SWA)": (
                "Each local layer attends only to a fixed neighbourhood of tokens "
                "(window size = 64) instead of the full sequence. This keeps the "
                "attention cost linear in the window rather than quadratic in sequence length."
            ),
            "Alternating Local / Global Layers": (
                "Layers alternate: even-indexed layers use the local SWA window (64 tokens), "
                "odd-indexed layers attend to the full context. This lets the model capture "
                "both fine-grained local patterns and long-range dependencies cheaply."
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

    "Lexis 2": {
        "features": [
            "Grouped-Query Attention (GQA)",
            "RoPE",
            "SwiGLU",
            "RMSNorm",
        ],
        "details": {
            "Grouped-Query Attention (GQA)": (
                "GQA shares key/value heads across groups of query heads (4 KV heads for "
                "12 query heads here). This cuts the KV-cache memory by 3× versus "
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


# ── Model catalogue ───────────────────────────────────────────────────────────
# arch_family references a key in ARCHITECTURES — no per-model duplication.

AVAILABLE_MODELS = {
    "Lexis1-TS-1M": {
        "title": "Lexis 1 — TinyStories 1M",
        "description": (
            "A compact 1M-parameter model fine-tuned on the TinyStories dataset. "
            "Generates coherent short narratives with simple vocabulary. "
            "Designed to explore efficient attention patterns at tiny scale."
        ),
        "parameters": "1 Million",
        "disk_size_mb": 4,
        "category": "tiny_stories",
        "repo_id": f"{HF_USERNAME}/Lexis1-TS-1M",
        "tokenizer": "tiny_stories_unk",

        # ── Specs ──────────────────────────────────────────────────────────────
        "context_size": 512,
        "layers": 8,
        "attention_heads": 8,
        "embedding_dim": 128,
        "tokens_trained": "475 Million",

        # ── Architecture ───────────────────────────────────────────────────────
        "arch_family": "Lexis 1",

        # SWA-specific extras (Lexis 1 only)
        "swa_window_size": 64,
        "swa_pattern": "Even layers: local (w=64) · Odd layers: global (full context)",
    },

    "Lexis2-OS-110M": {
        "title": "Lexis 2 — OnlySports 110M",
        "description": (
            "A 110M-parameter model fine-tuned exclusively on sports content. "
            "Produces sports-domain text with accurate terminology and commentary style. "
            "Uses Grouped-Query Attention for a favourable quality-to-cost trade-off."
        ),
        "parameters": "110 Million",
        "disk_size_mb": 220,
        "category": "only_sports",
        "repo_id": f"{HF_USERNAME}/Lexis2-OS-110M",
        "tokenizer": "onlysports",

        # ── Specs ──────────────────────────────────────────────────────────────
        "context_size": 2048,
        "layers": 12,
        "attention_heads": 12,
        "kv_heads": 4,
        "embedding_dim": 768,
        "tokens_trained": "2.4 Billion",

        # ── Architecture ───────────────────────────────────────────────────────
        "arch_family": "Lexis 2",
    },
}