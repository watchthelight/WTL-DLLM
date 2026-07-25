# wtl-dllm · dllm/model/transformer.py
# what: pre-norm transformer, rope + sdpa, bidirectional by default, causal flag builds the ar twin
# why:  one trunk two behaviors — the diffusion/ar comparison must share every parameter shape
# by:   <wtl> watchthelight
# tags: model, transformer

import torch
import torch.nn as nn
import torch.nn.functional as F

from dllm.config import ModelPreset


def _rope_cache(ctx: int, head_dim: int, device, dtype):
    inv = 1.0 / (10000 ** (torch.arange(0, head_dim, 2, device=device) / head_dim))
    t = torch.arange(ctx, device=device)
    freqs = torch.outer(t, inv)
    return torch.cos(freqs).to(dtype), torch.sin(freqs).to(dtype)


def _apply_rope(x, cos, sin):
    # x: (B, H, L, D)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    L = x.shape[-2]
    c, s = cos[:L].unsqueeze(0).unsqueeze(0), sin[:L].unsqueeze(0).unsqueeze(0)
    out = torch.empty_like(x)
    out[..., 0::2] = x1 * c - x2 * s
    out[..., 1::2] = x1 * s + x2 * c
    return out


class Block(nn.Module):
    def __init__(self, d: int, heads: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.proj = nn.Linear(d, d, bias=False)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(
            nn.Linear(d, 4 * d, bias=False), nn.GELU(), nn.Linear(4 * d, d, bias=False)
        )
        self.heads = heads

    def forward(self, x, cos, sin, causal: bool):
        B, L, D = x.shape
        q, k, v = self.qkv(self.ln1(x)).chunk(3, dim=-1)
        q = q.view(B, L, self.heads, -1).transpose(1, 2)
        k = k.view(B, L, self.heads, -1).transpose(1, 2)
        v = v.view(B, L, self.heads, -1).transpose(1, 2)
        q, k = _apply_rope(q, cos, sin), _apply_rope(k, cos, sin)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=causal)
        y = y.transpose(1, 2).reshape(B, L, D)
        x = x + self.proj(y)
        return x + self.mlp(self.ln2(x))


class Transformer(nn.Module):
    def __init__(self, preset: ModelPreset, vocab_size: int, causal: bool = False):
        super().__init__()
        self.preset, self.causal = preset, causal
        self.emb = nn.Embedding(vocab_size, preset.d_model)
        self.blocks = nn.ModuleList(Block(preset.d_model, preset.n_heads) for _ in range(preset.n_layers))
        self.ln_f = nn.LayerNorm(preset.d_model)
        self.head = nn.Linear(preset.d_model, vocab_size, bias=False)
        self.apply(self._init)
        head_dim = preset.d_model // preset.n_heads
        cos, sin = _rope_cache(preset.ctx, head_dim, "cpu", torch.float32)
        self.register_buffer("rope_cos", cos, persistent=False)
        self.register_buffer("rope_sin", sin, persistent=False)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=0.02)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, std=0.02)

    def forward(self, ids):
        x = self.emb(ids)
        cos = self.rope_cos.to(x.dtype)
        sin = self.rope_sin.to(x.dtype)
        for b in self.blocks:
            x = b(x, cos, sin, self.causal)
        return self.head(self.ln_f(x))

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())
