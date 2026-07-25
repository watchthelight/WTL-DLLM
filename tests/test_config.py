# wtl-dllm · tests/test_config.py
# what: presets instantiate and param estimates land near their labels
# by:   <wtl> watchthelight
# tags: tests, config

from dllm.config import PRESETS, default_preset, estimate_params


def test_presets_instantiate():
    for name, p in PRESETS.items():
        assert p.name == name
        assert p.d_model % p.n_heads == 0


def test_param_estimates_near_labels():
    labels = {"cpu-5m": 5e6, "gpu-10m": 10e6, "gpu-17m": 17e6, "gpu-30m": 30e6}
    for name, target in labels.items():
        est = estimate_params(PRESETS[name])
        assert abs(est - target) / target < 0.15, f"{name}: {est:,}"


def test_default_preset_resolves():
    assert default_preset().name in PRESETS
