# wtl-dllm · tests/test_train_smoke.py
# what: 60-step smoke on cpu — loss falls, checkpoint loads, resume continues
# by:   <wtl> watchthelight
# tags: tests, train

import json
import sys

import pytest
import torch

from dllm.data.build import build_level
from dllm.train import trainer


@pytest.fixture(scope="module")
def tiny_data(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    build_level(1, n_train=2000, n_eval=50, seed=5, out=out)
    return out


def _run(mode, tmp, data_dir, steps, resume=False, monkeypatch=None):
    argv = ["trainer", "--preset", "cpu-5m", "--level", "1", "--steps", str(steps),
            "--mode", mode, "--run-name", f"smoke-{mode}", "--data-dir", str(data_dir)]
    if resume:
        argv.append("--resume")
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(trainer, "ROOT", tmp)
    trainer.main()
    return tmp / "runs" / "ckpt" / f"smoke-{mode}"


@pytest.mark.parametrize("mode", ["diffusion", "ar"])
def test_smoke_train_and_resume(mode, tiny_data, tmp_path, monkeypatch):
    out = _run(mode, tmp_path, tiny_data, 60, monkeypatch=monkeypatch)
    metrics = [json.loads(l) for l in (out / "metrics.jsonl").read_text().splitlines()
               if "loss" in l]
    assert metrics, "no metrics logged"
    # initial CE is ln(vocab) ~ 3.09; anything well under that by step ~50 means learning
    late = metrics[-1]["loss"]
    assert late < 1.5, f"{mode}: loss stuck at {late:.3f} (init ~3.09)"

    ck = torch.load(sorted(out.glob("step*.pt"))[-1], map_location="cpu", weights_only=False)
    assert ck["step"] == 60 and ck["mode"] == mode

    _run(mode, tmp_path, tiny_data, 80, resume=True, monkeypatch=monkeypatch)
    ck2 = torch.load(sorted(out.glob("step*.pt"))[-1], map_location="cpu", weights_only=False)
    assert ck2["step"] == 80
