import math

from torch import nn
import torch
import torch.nn.functional as F
from torch.nn.attention.flex_attention import flex_attention, create_block_mask

from src.models.base import BaseTransformer
from src.models.model_config import Lexis1ModelConfig

class CausalSelfAttention(nn.Module):
    def __init__(self, config: Lexis1ModelConfig, attn_type: str = "global"):
        super().__init__()
        assert config.n_embd % config.n_head == 0

        self.n_head = config.n_head
        self.n_embd = config.n_embd
        self.head_dim = self.n_embd // self.n_head

        self.c_q = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_k = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_v = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd)

        self.flash_attention: bool = config.flash_attention
        self.attn_type = attn_type # global or local for sliding window attention
        self.window_size = config.window_size # Default window size

        if self.flash_attention and self.attn_type == "local":
            # https://pytorch.org/blog/flexattention/
            def sliding_window_causal(b, h, q_idx, kv_idx):
                causal_mask = q_idx >= kv_idx
                window_mask = q_idx - kv_idx < self.window_size 
                return causal_mask & window_mask
            
            self.block_mask = create_block_mask(
                sliding_window_causal, 
                1, 1,
                config.block_size, 
                config.block_size
            )
        else:
            self.block_mask = None

        mask = torch.tril(torch.ones(config.block_size, config.block_size))
        if self.attn_type == "local":
            local_mask = torch.triu(
                torch.ones(config.block_size, config.block_size), 
                diagonal=-self.window_size + 1
            )
            mask = mask * local_mask
        self.register_buffer("attn_mask", mask.view(1, 1, config.block_size, config.block_size))
    
    def forward(self, x):
        B, T, C = x.size()

        q = self.c_q(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2) # (B, nh, T, hs)
        k = self.c_k(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2) # (B, nh, T, hs)
        v = self.c_v(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2) # (B, nh, T, hs)

        if self.flash_attention:
            if self.attn_type == "global":
                y = F.scaled_dot_product_attention(
                    q, k, v,
                    attn_mask=None,
                    dropout_p=0.0,
                    is_causal=True
                )
            else:
                # Sliding Window Attention
                #! This is only available if the embedding head dimension (n_embd/n_head) is greater or equal than 16
                if self.block_mask.shape[-1] != T:
                    def sliding_window_causal(b, h, q_idx, kv_idx):
                        causal_mask = q_idx >= kv_idx
                        window_mask = q_idx - kv_idx < self.window_size
                        return causal_mask & window_mask
                    block_mask = create_block_mask(sliding_window_causal, 1, 1, T, T)
                else:
                    block_mask = self.block_mask
                y = flex_attention(q, k, v, block_mask=block_mask)
        else:
            att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1))) # (B, nh, T, T)
            att = att.masked_fill(self.attn_mask[:, :, :T, :T] == 0, float('-inf')) # (B, nh, T, T)
            att = F.softmax(att, dim=-1) # (B, nh, T, T)
            y = att @ v # (B, nh, T, hs)

        y = y.transpose(1, 2).contiguous().view(B, T, C) # re-assemble all head outputs side by side
        # output projection
        y = self.c_proj(y)
        return y


class MLP(nn.Module):
    def __init__(self, config: Lexis1ModelConfig):
        super().__init__()
        self.c_fc = nn.Linear(config.n_embd, 4 * config.n_embd)
        self.gelu = nn.GELU(approximate='tanh')
        self.c_proj = nn.Linear(4 * config.n_embd, config.n_embd)
    
    def forward(self, x):
        x = self.c_fc(x)
        x = self.gelu(x)
        x = self.c_proj(x)
        return x


class Block(nn.Module):
    def __init__(self, config: Lexis1ModelConfig, attn_type: str):
        super().__init__()
        self.ln_1 = nn.LayerNorm(config.n_embd)
        self.attn = CausalSelfAttention(config, attn_type=attn_type)
        self.ln_2 = nn.LayerNorm(config.n_embd)
        self.mlp = MLP(config)
    
    def forward(self, x):
        # We do pre-layernorm (before each layer)
        x = x + self.attn(self.ln_1(x))
        x = x + self.mlp(self.ln_2(x))
        return x
    

class Lexis1(BaseTransformer):
    def __init__(self, config: Lexis1ModelConfig):
        super().__init__(config=config)

        attn_layers = config.attn_layers
        assert len(attn_layers) == config.n_layer, "attn_layers doesn't have length of n_layer"
        
        self.transformer = nn.ModuleDict(dict(
            wte=nn.Embedding(config.vocab_size, config.n_embd), # token embedding table
            wpe=nn.Embedding(config.block_size, config.n_embd), # position embedding table
            h=nn.ModuleList([Block(config, attn_layers[i]) for i in range(config.n_layer)]), # transformer blocks
            ln_f=nn.LayerNorm(config.n_embd), # final layer norm
        ))
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # shared input and output matrices
        self.transformer.wte.weight = self.lm_head.weight
    
    def forward(self, idx):
        _, T = idx.size()
        assert T <= self.config.block_size, "Cannot forward, model block size is exhausted."

        # pos is a tensor of shape (T,) containing the position indices from 0 to T-1.
        pos = torch.arange(0, T, dtype=torch.long, device=idx.device) # (T,)
        pos_emb = self.transformer.wpe(pos) # (T, n_embd)

        tok_emb = self.transformer.wte(idx) # (B, T, n_embd)

        x = tok_emb + pos_emb # (B, T, n_embd)

        for block in self.transformer.h:
            x = block(x)

        x = self.transformer.ln_f(x) # (B, T, n_embd) final layer norm
        logits = self.lm_head(x) # (B, T, vocab_size)

        return logits