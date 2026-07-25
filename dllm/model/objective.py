# wtl-dllm · dllm/model/objective.py
# what: masked-diffusion loss (llada guidelines recipe) + ar twin loss
# why:  the whole method is these ~30 lines; get them boring and right
# by:   <wtl> watchthelight
# tags: model, objective, diffusion

import torch
import torch.nn.functional as F

EPS = 1e-3


def diffusion_loss(model, x, prompt_lens=None, antithetic=False, generator=None):
    """x: (B, L) clean ids. prompt_lens: (B,) — positions < prompt_len are never masked.

    t ~ U(0,1) per sequence; p_mask = (1-eps)*t + eps; mask i.i.d.;
    CE on masked positions, each term / p_mask, averaged over B*L.
    No time conditioning anywhere — the model never sees t.
    """
    B, L = x.shape
    dev = x.device
    t = torch.rand(B, device=dev, generator=generator)
    if antithetic:
        half = B // 2
        t = torch.cat([t[:half], 1.0 - t[:half]], dim=0)[:B]
    p_mask = (1 - EPS) * t + EPS                          # (B,)
    mask = torch.rand(B, L, device=dev, generator=generator) < p_mask[:, None]
    if prompt_lens is not None:
        pos = torch.arange(L, device=dev)[None, :]
        mask &= pos >= prompt_lens[:, None]
    if not mask.any():
        return None
    from dllm.data.generator import VOCAB
    mask_id = VOCAB.index("[MASK]")
    noisy = torch.where(mask, torch.full_like(x, mask_id), x)
    logits = model(noisy)
    ce = F.cross_entropy(logits[mask], x[mask], reduction="none")
    weights = p_mask[:, None].expand(B, L)[mask]
    return (ce / weights).sum() / (B * L)


def ar_loss(model, x, prompt_lens=None, pad_id=None):
    """Next-token CE for the twin. Loss only where the diffusion model pays it:
    answer region (>= prompt_len) — apples to apples."""
    logits = model(x[:, :-1])
    targets = x[:, 1:].clone()
    B, Lm1 = targets.shape
    if prompt_lens is not None:
        pos = torch.arange(1, Lm1 + 1, device=x.device)[None, :]
        targets[pos < prompt_lens[:, None]] = -100
    return F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1),
                           ignore_index=-100)


def shorten_canvas(x, min_lens):
    """1% trick: truncate the pad tail to a random shorter canvas (content survives)."""
    L = x.shape[1]
    floor = int(min_lens.max().item())
    if floor >= L:
        return x
    new_len = int(torch.randint(floor, L + 1, (1,)).item())
    return x[:, :new_len]
