# wtl-dllm · dllm/model/sampler.py
# what: maskgit-style unmasking loop with per-step frame capture, four orderings, infill
# why:  the ui replays these frames; committed tokens are frozen and stay frozen
# by:   <wtl> watchthelight
# tags: sampler, inference

import math

import torch

ORDERINGS = ("random", "confidence", "margin", "entropy")


def _commit_counts(n_masked: int, steps: int) -> list[int]:
    """Cosine schedule over remaining masks: few early, many late, >=1 per step, sums to n_masked."""
    remaining = [int(math.floor(n_masked * math.cos(math.pi / 2 * s / steps))) for s in range(1, steps + 1)]
    remaining[-1] = 0
    counts, prev = [], n_masked
    for r in remaining:
        r = min(r, prev - 1)  # force progress
        counts.append(prev - max(r, 0))
        prev = max(r, 0)
        if prev == 0:
            break
    return counts


@torch.no_grad()
def _core_loop(model, tok, ids, steps, ordering, temperature, seed, capture):
    """Unmask a partially-masked canvas in place. Committed positions never change."""
    assert ordering in ORDERINGS, f"ordering must be one of {ORDERINGS}"
    was_training = model.training
    model.eval()
    device = ids.device
    gen = torch.Generator(device="cpu").manual_seed(seed) if seed is not None else None

    committed = ids != tok.mask_id
    conf_val = torch.zeros(ids.shape[0], device=device)
    conf_val[committed] = 1.0  # given, not predicted

    n_masked = int((~committed).sum())
    if n_masked == 0:
        return ids.tolist(), []
    steps = steps or n_masked
    counts = _commit_counts(n_masked, min(steps, n_masked))
    frames, total = [], len(counts)

    for step, k in enumerate(counts, start=1):
        logits = model(ids[None])[0].float()
        probs = logits.softmax(-1)

        if temperature > 0:
            # float64 gumbel — float32 silently lowers effective temperature (arXiv 2409.02908)
            u = torch.rand(logits.shape, dtype=torch.float64, generator=gen).to(device)
            gumbel = -torch.log(-torch.log(u.clamp_min(1e-300)))
            choice = (logits.double() / temperature + gumbel).argmax(-1)
        else:
            choice = probs.argmax(-1)
        chosen_p = probs.gather(-1, choice[:, None]).squeeze(-1)

        masked_idx = (~committed).nonzero(as_tuple=True)[0]
        if ordering == "confidence":
            score = chosen_p[masked_idx]
        elif ordering == "margin":
            top2 = probs[masked_idx].topk(2, dim=-1).values
            score = top2[:, 0] - top2[:, 1]
        elif ordering == "entropy":
            p = probs[masked_idx]
            score = (p * p.clamp_min(1e-12).log()).sum(-1)  # -H; higher = more certain
        else:
            score = torch.rand(len(masked_idx), generator=gen).to(device)

        pick = masked_idx[score.topk(min(k, len(masked_idx))).indices]
        ids[pick] = choice[pick]
        committed[pick] = True
        conf_val[pick] = chosen_p[pick]

        if capture:
            frames.append({
                "step": step, "total_steps": total,
                "tokens": tok.decode_raw(ids.tolist()),
                "committed": committed.tolist(),
                "conf": [round(float(c), 4) for c in conf_val],
                "just_committed": sorted(int(i) for i in pick),
                "done": False,
            })

    if capture and frames:
        frames[-1] = {**frames[-1], "done": True, "answer": tok.decode(ids.tolist())}
    if was_training:
        model.train()
    return ids.tolist(), frames


def generate(model, tok, prompt_ids, canvas_len, steps=None, ordering="confidence",
             temperature=0.0, seed=None, capture=True):
    """Prompt fixed at the left, the rest of the canvas diffuses."""
    device = next(model.parameters()).device
    ids = torch.full((canvas_len,), tok.mask_id, dtype=torch.long, device=device)
    ids[: len(prompt_ids)] = torch.tensor(prompt_ids, dtype=torch.long, device=device)
    return _core_loop(model, tok, ids, steps, ordering, temperature, seed, capture)


def infill(model, tok, prefix_ids, suffix_ids, hole_len, **kw):
    """Prefix and suffix stay fixed; the hole diffuses — the demo ar structurally cannot do."""
    device = next(model.parameters()).device
    canvas_len = len(prefix_ids) + hole_len + len(suffix_ids)
    ids = torch.full((canvas_len,), tok.mask_id, dtype=torch.long, device=device)
    ids[: len(prefix_ids)] = torch.tensor(prefix_ids, dtype=torch.long, device=device)
    if suffix_ids:
        ids[len(prefix_ids) + hole_len:] = torch.tensor(suffix_ids, dtype=torch.long, device=device)
    return _core_loop(model, tok, ids, kw.pop("steps", None), kw.pop("ordering", "confidence"),
                      kw.pop("temperature", 0.0), kw.pop("seed", None), kw.pop("capture", True))


def generate_blockwise(model, tok, prompt_ids, canvas_len, block_len=8, **kw):
    """Semi-ar stub: left-to-right blocks, diffusion inside each. Later milestone —
    kept minimal on purpose (see plan/07-sampling.md)."""
    device = next(model.parameters()).device
    ids = torch.full((canvas_len,), tok.mask_id, dtype=torch.long, device=device)
    ids[: len(prompt_ids)] = torch.tensor(prompt_ids, dtype=torch.long, device=device)
    frames_all = []
    pos = len(prompt_ids)
    while pos < canvas_len:
        end = min(pos + block_len, canvas_len)
        result_ids, frames = _core_loop(model, tok, ids[:end].clone(), None,
                                        kw.get("ordering", "confidence"),
                                        kw.get("temperature", 0.0), kw.get("seed"),
                                        kw.get("capture", True))
        ids[pos:end] = torch.tensor(result_ids[pos:end], dtype=torch.long, device=device)
        frames_all.extend(frames)
        pos = end
    return ids.tolist(), frames_all
