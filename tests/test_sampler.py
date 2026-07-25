# wtl-dllm · tests/test_sampler.py
# what: determinism, frozen-commit invariant, prompt protection, infill, orderings
# by:   <wtl> watchthelight
# tags: tests, sampler

import torch

from dllm.config import PRESETS
from dllm.model import Tokenizer, Transformer
from dllm.model.sampler import ORDERINGS, _commit_counts, generate, generate_blockwise, infill

TINY = PRESETS["cpu-5m"]


def _mt():
    torch.manual_seed(0)
    tok = Tokenizer()
    return tok, Transformer(TINY, len(tok)).eval()


def test_commit_counts_sum_and_progress():
    for n in (1, 2, 5, 12, 31):
        for s in (1, 3, n):
            c = _commit_counts(n, max(s, 1))
            assert sum(c) == n and all(k >= 1 for k in c)


def test_determinism_temp0_and_hot():
    tok, m = _mt()
    prompt = [tok.t2i[c] for c in "47+58="]
    for temp in (0.0, 0.7):
        a = generate(m, tok, prompt, 12, temperature=temp, seed=11)
        b = generate(m, tok, prompt, 12, temperature=temp, seed=11)
        assert a[0] == b[0] and a[1] == b[1]


def test_frozen_commit_invariant():
    tok, m = _mt()
    prompt = [tok.t2i[c] for c in "12*7="]
    _, frames = generate(m, tok, prompt, 12, ordering="confidence")
    prev = None
    for f in frames:
        if prev is not None:
            for i, was in enumerate(prev["committed"]):
                if was:
                    assert f["committed"][i], "committed became uncommitted"
                    assert f["tokens"][i] == prev["tokens"][i], "committed token changed"
        prev = f
    assert frames[-1]["done"] and "answer" in frames[-1]


def test_prompt_present_from_frame_zero():
    tok, m = _mt()
    prompt = [tok.t2i[c] for c in "9+9="]
    _, frames = generate(m, tok, prompt, 12)
    assert frames[0]["tokens"][:4] == ["9", "+", "9", "="]
    assert all(frames[0]["committed"][:4])


def test_steps_one_and_full():
    tok, m = _mt()
    prompt = [tok.t2i[c] for c in "5+5="]
    for steps in (1, 8):
        ids, frames = generate(m, tok, prompt, 12, steps=steps)
        assert tok.mask_id not in ids
        assert len(frames) <= steps if steps > 1 else len(frames) == 1


def test_infill_preserves_context():
    tok, m = _mt()
    pre = [tok.t2i[c] for c in "18+"]
    suf = [tok.t2i[c] for c in "=45"]
    ids, frames = infill(m, tok, pre, suf, hole_len=2, seed=3)
    toks = frames[-1]["tokens"]
    assert toks[:3] == ["1", "8", "+"] and toks[-3:] == ["=", "4", "5"]
    assert tok.mask_id not in ids


def test_orderings_change_commit_order():
    tok, m = _mt()
    prompt = [tok.t2i[c] for c in "47+58="]
    orders = {}
    for o in ORDERINGS:
        _, frames = generate(m, tok, prompt, 12, ordering=o, seed=5)
        orders[o] = tuple(tuple(f["just_committed"]) for f in frames)
    assert len(set(orders.values())) > 1, "all orderings identical — flag is dead"


def test_blockwise_stub_terminates():
    tok, m = _mt()
    prompt = [tok.t2i[c] for c in "3+4="]
    ids, frames = generate_blockwise(m, tok, prompt, 12, block_len=4)
    assert len(ids) == 12 and tok.mask_id not in ids and frames
