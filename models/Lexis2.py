import math

from torch import nn
import torch
import torch.nn.functional as F
import bitsandbytes as bnb
from models.RoPE import RotaryEmbedding, apply_rotary_emb
from models.base import BaseTransformer
from models.model_config import Lexis2ModelConfig


class CausalSelfAttention(nn.Module):
    def __init__(self, config: Lexis2ModelConfig):
        super().__init__()
        assert config.n_embd % config.n_head == 0
        assert config.n_head % config.n_kv_head == 0

        self.n_head = config.n_head
        self.n_kv_head = config.n_kv_head
        self.n_embd = config.n_embd
        self.head_dim = self.n_embd // self.n_head
        self.kv_groups = self.n_head // self.n_kv_head # number of groups of heads that share the same K and V

        self.c_q = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_k = nn.Linear(self.n_embd, self.n_kv_head * self.head_dim, bias=False)
        self.c_v = nn.Linear(self.n_embd, self.n_kv_head * self.head_dim, bias=False)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd, bias=False)

        self.flash_attention: bool = config.flash_attention

        # Attention dropout: applied to the attention weight matrix (post-softmax)
        # before the weighted sum with V. Prevents individual heads from dominating.
        self.attn_dropout = nn.Dropout(config.dropout)

        # RoPE: one shared instance per attention layer, applied to Q and K.
        self.rotary_emb = RotaryEmbedding(
            dim=self.head_dim,
            max_seq_len=config.block_size,
            base=config.rope_base,
        )

        mask = torch.tril(torch.ones(config.block_size, config.block_size))
        self.register_buffer("attn_mask", mask.view(1, 1, config.block_size, config.block_size))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.size()

        q = self.c_q(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2) # (B, n_head, T, head_dim)
        k = self.c_k(x).view(B, T, self.n_kv_head, self.head_dim).transpose(1, 2) # (B, n_kv_head, T, head_dim)
        v = self.c_v(x).view(B, T, self.n_kv_head, self.head_dim).transpose(1, 2) # (B, n_kv_head, T, head_dim)

        # Apply RoPE to Q and K
        cos, sin = self.rotary_emb(T)
        q, k = apply_rotary_emb(q, k, cos, sin)

        # Expand K/V heads to match Q heads by repeating each KV head kv_groups times.
        #  Objective: (B, n_kv_head, T, hs) -> (B, n_head, T, hs)
        # (B, n_kv_head, T, hs)
        # → unsqueeze(2) -> (B, n_kv_head, 1, T, hs)
        # → expand(...) -> (B, n_kv_head, kv_groups, T, hs) # zero-copy view
        # → reshape(...) -> (B, n_head, T, hs) # materialises contiguous tensor
        k = k.unsqueeze(2).expand(B, self.n_kv_head, self.kv_groups, T, self.head_dim) \
             .reshape(B, self.n_head, T, self.head_dim)
        v = v.unsqueeze(2).expand(B, self.n_kv_head, self.kv_groups, T, self.head_dim) \
             .reshape(B, self.n_head, T, self.head_dim)

        if self.flash_attention:
            y = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=None,
                dropout_p=self.attn_dropout.p if self.training else 0.0,
                is_causal=True
            )
        else:
            att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1))) # (B, nh, T, T)
            att = att.masked_fill(self.attn_mask[:, :, :T, :T] == 0, float('-inf')) # (B, nh, T, T)
            att = F.softmax(att, dim=-1) # (B, nh, T, T)
            att = self.attn_dropout(att) # Drop attention weights before weighted sum with V
            y = att @ v # (B, nh, T, hs)

        y = y.transpose(1, 2).contiguous().view(B, T, C) # re-assemble all head outputs side by side
        # output projection
        y = self.c_proj(y)
        return y


class SwiGLU(nn.Module):
    def __init__(self, config: Lexis2ModelConfig):
        super().__init__()
        # First shrink hidden dim to 2/3 of the normal hidden size in standard transformers to keep parameter count equivalent
        # then round to multiple of 256 for better GPU utilization
        hidden_dim = 256 * ((int(4 * config.n_embd * 2 / 3) + 255) // 256)

        self.W1 = nn.Linear(config.n_embd, hidden_dim, bias=False)  # gate
        self.W3 = nn.Linear(config.n_embd, hidden_dim, bias=False)  # value
        self.W2 = nn.Linear(hidden_dim, config.n_embd, bias=False)  # output projection

        # FFN internal dropout: applied after the SwiGLU gated activation,
        # before the output projection. Prevents co-adaptation inside the FFN block.
        self.ffn_dropout = nn.Dropout(config.dropout)

    def forward(self, x):
        # SwiGLU: https://arxiv.org/abs/2002.05202
        # Dropout is placed after the gated activation and before W2 (the output projection).
        return self.W2(self.ffn_dropout(F.silu(self.W1(x)) * self.W3(x)))


class Block(nn.Module):
    def __init__(self, config: Lexis2ModelConfig):
        super().__init__()
        self.ln_1 = nn.RMSNorm(config.n_embd)
        self.attn = CausalSelfAttention(config)
        self.ln_2 = nn.RMSNorm(config.n_embd)
        self.mlp = SwiGLU(config)

        # Residual dropout: applied to each sublayer's output before it is added
        # back to the residual stream.
        self.resid_dropout = nn.Dropout(config.dropout)
    
    def forward(self, x):
        # Pre-RMSNorm style (normalize input, not output).
        # Dropout is applied to each sublayer output before the residual add,
        # matching the formulation: x = x + Dropout(Sublayer(Norm(x)))
        x = x + self.resid_dropout(self.attn(self.ln_1(x)))
        x = x + self.resid_dropout(self.mlp(self.ln_2(x)))
        return x
    

class Lexis2(BaseTransformer):
    def __init__(self, config: Lexis2ModelConfig):
        super().__init__(config=config)
        
        self.transformer = nn.ModuleDict(dict(
            wte=nn.Embedding(config.vocab_size, config.n_embd), # token embedding table
            dropout=nn.Dropout(config.dropout), # embedding dropout
            h=nn.ModuleList([Block(config) for _ in range(config.n_layer)]), # transformer blocks
            ln_f=nn.RMSNorm(config.n_embd), # final layer norm
        ))
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # Weight tying: share token embedding and output projection matrices
        self.transformer.wte.weight = self.lm_head.weight
    
    def forward(self, idx):
        _, T = idx.size()
        assert T <= self.config.block_size, "Cannot forward, model block size is exhausted."

        x = self.transformer.wte(idx) # (B, T, n_embd)

        x = self.transformer.dropout(x) # (B, T, n_embd) apply dropout to the embeddings

        for block in self.transformer.h:
            x = block(x)

        x = self.transformer.ln_f(x) # (B, T, n_embd) final layer norm
        logits = self.lm_head(x) # (B, T, vocab_size)

        return logits