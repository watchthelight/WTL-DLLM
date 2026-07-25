# wtl-dllm · dllm/config.py
# what: model presets + training defaults, keyed off the probed environment
# why:  one place decides sizes; everything else asks here
# by:   <wtl> watchthelight
# tags: core, config

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_JSON = ROOT / "docs" / "results" / "env.json"


@dataclass(frozen=True)
class ModelPreset:
    name: str
    d_model: int
    n_layers: int
    n_heads: int
    ctx: int
    batch_size: int


@dataclass(frozen=True)
class TrainDefaults:
    lr: float = 3e-4
    betas: tuple = (0.9, 0.95)
    weight_decay: float = 0.1
    warmup_frac: float = 0.03
    min_lr_frac: float = 0.1
    grad_clip: float = 1.0
    ema_decay: float = 0.995  # deliberately not 0.9999 — short runs, see dossier
    eps_mask: float = 1e-3
    log_every: int = 50
    ckpt_every: int = 1000
    sample_every: int = 1000


PRESETS = {
    "cpu-5m": ModelPreset("cpu-5m", 256, 6, 8, 64, 64),
    "gpu-10m": ModelPreset("gpu-10m", 320, 8, 8, 96, 256),
    "gpu-17m": ModelPreset("gpu-17m", 448, 8, 8, 128, 192),
    "gpu-30m": ModelPreset("gpu-30m", 512, 10, 8, 128, 128),
}


def estimate_params(p: ModelPreset, vocab_size: int = 22) -> int:
    emb = vocab_size * p.d_model
    head = p.d_model * vocab_size
    blocks = 12 * p.n_layers * p.d_model**2  # 4d^2 attention + 8d^2 mlp
    norms = (2 * p.n_layers + 1) * p.d_model
    return emb + head + blocks + norms


def default_preset() -> ModelPreset:
    name = "cpu-5m"
    if ENV_JSON.exists():
        rec = json.loads(ENV_JSON.read_text()).get("preset_recommendation")
        if rec in PRESETS:
            name = rec
    return PRESETS[name]
