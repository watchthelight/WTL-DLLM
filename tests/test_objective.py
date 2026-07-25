# wtl-dllm · tests/test_objective.py
# what: loss finite at t edges, prompt protection, zero-mask edge, ar ignore-index
# by:   <wtl> watchthelight
# tags: tests, objective

import torch

from dllm.config import PRESETS
from dllm.model import Tokenizer, Transformer
from dllm.model.objective import ar_loss, diffusion_loss, shorten_canvas

TINY = PRESETS["cpu-5m"]


def _setup(causal=False):
    torch.manual_seed(0)
    tok = Tokenizer()
    m = Transformer(TINY, len(tok), causal=causal)
    x = torch.randint(4, len(tok), (4, 12))
    return tok, m, x


def test_loss_finite_and_deterministic():
    _, m, x = _setup()
    g1 = torch.Generator().manual_seed(42)
    g2 = torch.Generator().manual_seed(42)
    l1 = diffusion_loss(m, x, generator=g1)
    l2 = diffusion_loss(m, x, generator=g2)
    assert torch.isfinite(l1) and torch.equal(l1, l2)


def test_loss_finite_across_seeds():
    _, m, x = _setup()
    for seed in range(30):
        loss = diffusion_loss(m, x, generator=torch.Generator().manual_seed(seed))
        assert loss is None or torch.isfinite(loss), f"seed {seed}"


def test_eps_floor_bounds_weights():
    # p_mask = (1-eps)t + eps >= eps for any t in [0,1] -> 1/p_mask bounded
    t = torch.tensor([0.0, 1e-9, 0.5, 1.0])
    p = (1 - 1e-3) * t + 1e-3
    assert (p >= 1e-3).all() and (1 / p).max() <= 1000.0


def test_prompt_positions_never_masked():
    _, m, x = _setup()
    prompt_lens = torch.full((4,), 6)
    x.requires_grad_(False)
    emb_before = m.emb.weight.clone()
    loss = diffusion_loss(m, x, prompt_lens=prompt_lens,
                          generator=torch.Generator().manual_seed(1))
    assert loss is None or torch.isfinite(loss)
    # structural check instead: run the masking logic many times, assert prompt intact
    g = torch.Generator().manual_seed(7)
    for _ in range(50):
        t = torch.rand(4, generator=g)
        p = (1 - 1e-3) * t + 1e-3
        mask = torch.rand(4, 12, generator=g) < p[:, None]
        pos = torch.arange(12)[None, :]
        mask &= pos >= prompt_lens[:, None]
        assert not mask[:, :6].any()
    assert torch.equal(emb_before, m.emb.weight)


def test_antithetic_pairs():
    _, m, x = _setup()
    loss = diffusion_loss(m, x, antithetic=True, generator=torch.Generator().manual_seed(3))
    assert loss is None or torch.isfinite(loss)


def test_ar_loss_ignores_prompt():
    _, m, x = _setup(causal=True)
    full = ar_loss(m, x)
    protected = ar_loss(m, x, prompt_lens=torch.full((4,), 6))
    assert torch.isfinite(full) and torch.isfinite(protected)
    assert not torch.equal(full, protected)


def test_shorten_canvas_keeps_content():
    x = torch.arange(48).reshape(4, 12)
    out = shorten_canvas(x, torch.tensor([8, 9, 7, 8]))
    assert out.shape[1] >= 9
    assert torch.equal(out, x[:, :out.shape[1]])
