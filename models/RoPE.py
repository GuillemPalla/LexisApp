import torch
from torch import nn

# ---------------------------------------------------------------------------
# Rotary Positional Embedding (RoPE)
#
# References:
#   [1] Su et al., "RoFormer: Enhanced Transformer with Rotary Position
#       Embedding", 2021 — https://arxiv.org/abs/2104.09864
#   [2] LLaMA / HuggingFace Transformers reference implementation:
#       https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py
# ---------------------------------------------------------------------------

class RotaryEmbedding(nn.Module):
    """
    Precomputes and caches the cos/sin tables for RoPE.

    For a head dimension `dim` and a sequence of positions 0..T-1, we
    compute frequency θ_i = 1 / (base^(2i/dim)) for i in [0, dim/2),
    then build cos(m·θ) and sin(m·θ) for every position m.

    The cache is extended on demand when a longer sequence is seen.
    """

    def __init__(self, dim: int, max_seq_len: int, base: float = 10_000.0):
        super().__init__()
        self.dim = dim
        self.base = base
        # Create the frequency table for RoPE. This is a 1D tensor of size (dim/2,).
        # θ_i = 1 / (base^(2i / dim)),  i = 0, 1, ..., dim/2 - 1
        # Instead of multilying the exponent by 2, we can just use the even indices (0, 2, 4, ...) in the arange.
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._build_cache(max_seq_len)

    def _build_cache(self, seq_len: int):
        """Build cos/sin tables up to seq_len."""
        # Create a tensor of shape (seq_len,) containing the position indices 0, 1, ..., seq_len-1.
        t = torch.arange(seq_len, device=self.inv_freq.device).float()

        # Compute the outer product of the position indices and the frequency table to get a (seq_len, dim/2) tensor of angles.
        # Every row corresponds to a position, and every column corresponds to a frequency. The (m, i)-th entry is m * θ_i.
        freqs = torch.outer(t, self.inv_freq) # (seq_len, dim/2)

        # Duplicate frequencies, because we rotate pairs of dimensions together.
        # This distributes the frequencies across the head dimension, so that every pair of 
        # dimensions (2i, 2i+1) gets the same frequency θ_i.
        emb = torch.cat([freqs, freqs], dim=-1) # (seq_len, dim)

        # Cache the cos and sin tables as buffers. We add two singleton dimensions at the front for broadcasting later
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :], persistent=False) # (1,1,T,dim)
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :], persistent=False)

    def forward(self, seq_len: int):
        if seq_len > self.cos_cached.shape[2]:
            self._build_cache(seq_len)
        return (
            self.cos_cached[:, :, :seq_len, :], # (1, 1, T, dim)
            self.sin_cached[:, :, :seq_len, :],
        )


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    """
    Perform the '90-degree rotation' part of Rotary Positional Embedding (RoPE).

    ------------------------------------------------------------
    WHAT THIS FUNCTION DOES
    ------------------------------------------------------------

    This function rearranges the tensor so that:

        (x1, x2)  →  (-x2, x1)

    This corresponds to multiplying each pair of dimensions by:

        [ 0  -1 ]
        [ 1   0 ]

    which is the matrix for a 90° rotation.

    This is later combined with cosine and sine terms to produce
    the full rotation:

        x_rot = x * cos + rotate_half(x) * sin

    which equals the standard 2-D rotation formula.

    ------------------------------------------------------------
    INPUT SHAPE
    ------------------------------------------------------------

    x shape:
        (..., head_dim)

    where:
        ...        = any leading dimensions
                     (batch, heads, sequence, etc.)

        head_dim   = must be EVEN
                     (because we rotate pairs of values)

    Example:

        x shape: (B, n_heads, T, 8)

        last dimension (8) represents:

            [x0 x1 x2 x3 x4 x5 x6 x7]

    ------------------------------------------------------------
    STEP 1 — Split the last dimension into two halves
    ------------------------------------------------------------

    We divide the vector into:

        first_half  = x[..., :half_dim]
        second_half = x[..., half_dim:]

    Example:

        x = [x0 x1 x2 x3 | x4 x5 x6 x7]

        first_half  = [x0 x1 x2 x3]
        second_half = [x4 x5 x6 x7]

    """

    # Size of the last dimension
    head_dim = x.shape[-1]

    # We rotate pairs → must split into two equal halves
    half_dim = head_dim // 2

    # Extract first half of dimensions
    first_half = x[..., :half_dim]

    # Extract second half of dimensions
    second_half = x[..., half_dim:]

    """
    ------------------------------------------------------------
    STEP 2 — Perform the 90° rotation
    ------------------------------------------------------------

    We compute:

        [-second_half, first_half]

    Example:

        first_half  = [x0 x1 x2 x3]
        second_half = [x4 x5 x6 x7]

        rotated = [-x4 -x5 -x6 -x7  x0 x1 x2 x3]

    This corresponds to:

        (x1, x2) → (-x2, x1)

    which is the sine-part of the rotation matrix:

        [ 0  -1 ]
        [ 1   0 ]

    """

    rotated = torch.cat(
        (-second_half, first_half),  # concatenate along last dimension
        dim=-1
    )

    return rotated



def apply_rotary_emb(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Apply Rotary Positional Embeddings (RoPE) to query and key tensors.

    ------------------------------------------------------------
    WHAT THIS FUNCTION DOES
    ------------------------------------------------------------

    For each position in the sequence, this function rotates the
    query (Q) and key (K) vectors by an angle that depends on:

        - the token position
        - the frequency assigned to each dimension

    The mathematical formula applied is:

        x_rot = x * cos(theta)
              + rotate_half(x) * sin(theta)

    which is equivalent to:

        [ cosθ  -sinθ ]
        [ sinθ   cosθ ]

    applied to every pair of dimensions.

    This operation encodes positional information directly into
    vector directions.

    ------------------------------------------------------------
    INPUT SHAPES
    ------------------------------------------------------------

    q shape:
        (B, n_heads, T, head_dim)

    k shape:
        (B, n_heads, T, head_dim)

    where:

        B         = batch size
        n_heads   = number of attention heads
        T         = sequence length
        head_dim  = dimension per head

    cos shape:
        (1, 1, T, head_dim)

    sin shape:
        (1, 1, T, head_dim)

    WHY cos/sin HAVE SHAPE (1,1,T,D):

        So broadcasting automatically applies the same
        rotation to:

            every batch
            every attention head

        without copying data.

    ------------------------------------------------------------
    STEP 1 — Rotate Q vectors
    ------------------------------------------------------------

    Compute:

        q_rot = q * cos + rotate_half(q) * sin

    This is exactly the expanded form of:

        2-D rotation matrix

    applied to each pair of dimensions.

    """

    # Compute the 90-degree rotated version of q
    q_rotated_half = _rotate_half(q)

    # Apply the full rotation formula
    #
    # q * cos       → cosine component
    # rotated * sin → sine component
    #
    # Broadcasting happens automatically here.
    q_rot = q * cos + q_rotated_half * sin

    """
    ------------------------------------------------------------
    STEP 2 — Rotate K vectors (same operation)
    ------------------------------------------------------------
    """

    k_rotated_half = _rotate_half(k)

    k_rot = k * cos + k_rotated_half * sin

    """
    ------------------------------------------------------------
    OUTPUT
    ------------------------------------------------------------

    Returns:

        q_rot : rotated query tensor
        k_rot : rotated key tensor

    Shapes remain:

        (B, n_heads, T, head_dim)

    Only the vector values change, not the dimensions.
    """

    return q_rot, k_rot