# wtl-dllm · tests/test_data.py
# what: generator determinism, vocab closure, validity per level, band disjointness
# by:   <wtl> watchthelight
# tags: tests, data

import re

from dllm.data.generator import CANVAS, VOCAB, MathGen, check_l5

CHARSET = set("".join(v for v in VOCAB if len(v) == 1))


def _batch(level, n=500, perturbed=False, seed=7):
    g = MathGen(seed, level, perturbed=perturbed)
    return [g.sample() for _ in range(n)]


def test_determinism():
    for level in CANVAS:
        assert _batch(level, 200) == _batch(level, 200)


def test_vocab_closure_and_canvas():
    for level in CANVAS:
        for s in _batch(level) + _batch(level, perturbed=True):
            assert set(s) <= CHARSET, f"stray char in {s!r}"
            assert len(s) + 1 <= CANVAS[level], f"too long for canvas: {s!r}"


def test_l1_l2_l3_arithmetic_valid():
    for level in (1, 2, 3):
        for s in _batch(level):
            left, expected = s.rsplit("=", 1)
            assert eval(left, {"__builtins__": {}}) == int(expected), s


def test_l2_division_exact():
    for s in _batch(2):
        if "/" in s:
            num, rest = s.split("/")
            den = rest.split("=")[0]
            assert int(num) % int(den) == 0, s


def test_l4_x_integer_and_consistent():
    for s in _batch(4):
        eq, xpart = s.split(",")
        x = int(xpart.removeprefix("x="))
        m = re.fullmatch(r"(\d+)x([+-])(\d+)=(\d+)", eq)
        assert m, s
        a, op, b, c = int(m[1]), m[2], int(m[3]), int(m[4])
        assert (a * x + b if op == "+" else a * x - b) == c, s


def test_l5_expressions_check_out():
    for s in _batch(5):
        assert check_l5(s), s


def test_perturbed_bands_disjoint():
    # every operand in perturbed ends in 8/9; train operands never do
    for level in CANVAS:
        train = set(_batch(level, 2000))
        pert = set(_batch(level, 2000, perturbed=True))
        assert not train & pert, f"L{level}: {sorted(train & pert)[:3]}"


def test_leakage_check_catches_plant():
    # same band -> same strings must collide, proving the check would fire
    a = set(_batch(1, 3000, seed=1))
    b = set(_batch(1, 3000, seed=2))
    assert a & b, "identical bands should collide; disjointness must come from bands, not luck"


def test_build_splits_disjoint(tmp_path):
    import json

    from dllm.data.build import build_level, is_heldout

    info = build_level(1, n_train=3000, n_eval=200, seed=11, out=tmp_path)
    assert info["eval_heldout"] == 200

    def texts(name):
        return {json.loads(l)["text"] for l in (tmp_path / f"{name}_l1.jsonl").read_text().splitlines()}

    train, held, pert = texts("train"), texts("eval_heldout"), texts("eval_perturbed")
    assert not train & held, "heldout leaked into train"
    assert not train & pert, "perturbed leaked into train"
    assert all(is_heldout(s) for s in held)
    assert not any(is_heldout(s) for s in train)
