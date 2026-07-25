# wtl-dllm · tests/test_model.py
# what: shapes, causality probe, param counts, tokenizer round-trip
# by:   <wtl> watchthelight
# tags: tests, model

import torch

from dllm.config import PRESETS
from dllm.data.generator import VOCAB, MathGen
from dllm.model import Tokenizer, Transformer

TINY = PRESETS["cpu-5m"]


def test_tokenizer_roundtrip():
    tok = Tokenizer()
    g = MathGen(3, 1)
    for _ in range(100):
        s = g.sample()
        ids = tok.encode(s, canvas=12)
        assert len(ids) == 12
        assert tok.decode(ids) == s


def test_forward_shapes():
    tok = Tokenizer()
    for causal in (False, True):
        m = Transformer(TINY, len(tok), causal=causal)
        x = torch.randint(0, len(tok), (2, 16))
        assert m(x).shape == (2, 16, len(tok))


def test_param_count_near_estimate():
    from dllm.config import estimate_params
    m = Transformer(TINY, len(VOCAB))
    est = estimate_params(TINY, len(VOCAB))
    assert abs(m.param_count() - est) / est < 0.05


def test_causal_flag_blocks_future():
    torch.manual_seed(0)
    tok = Tokenizer()
    m = Transformer(TINY, len(tok), causal=True).eval()
    x = torch.randint(4, len(tok), (1, 10))
    y = x.clone()
    y[0, -1] = (y[0, -1] + 1 - 4) % (len(tok) - 4) + 4
    with torch.no_grad():
        a, b = m(x), m(y)
    assert torch.allclose(a[0, :5], b[0, :5], atol=1e-5), "future token leaked into past logits"


def test_bidirectional_sees_future():
    torch.manual_seed(0)
    tok = Tokenizer()
    m = Transformer(TINY, len(tok), causal=False).eval()
    x = torch.randint(4, len(tok), (1, 10))
    y = x.clone()
    y[0, -1] = (y[0, -1] + 1 - 4) % (len(tok) - 4) + 4
    with torch.no_grad():
        a, b = m(x), m(y)
    assert not torch.allclose(a[0, 0], b[0, 0], atol=1e-6), "bidirectional model ignored context change"
