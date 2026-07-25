# wtl-dllm · dllm/serve/stub.py
# what: fake model+frames so the ui and server tests never wait on training
# by:   <wtl> watchthelight
# tags: serve, stub

from dllm.data.generator import CANVAS, MathGen, prompt_len
from dllm.model import Tokenizer


def stub_frames(level: int, seed: int = 0, steps: int | None = None):
    """Deterministic plausible frames: a real problem revealed over n steps."""
    tok = Tokenizer()
    text = MathGen(seed or 1, level).sample()
    canvas = CANVAS[level]
    ids = tok.encode(text, canvas=canvas)
    plen = prompt_len(text, level)
    hole = [i for i in range(len(ids)) if i >= plen]
    steps = steps or len(hole)
    per = max(len(hole) // steps, 1)

    committed = [i < plen for i in range(canvas)]
    tokens = [tok.vocab[i] if committed[j] else "[MASK]" for j, i in enumerate(ids)]
    conf = [1.0 if c else 0.0 for c in committed]
    frames, revealed = [], 0
    step = 0
    while revealed < len(hole):
        step += 1
        take = hole[revealed: revealed + per] if step < steps else hole[revealed:]
        for i in take:
            committed[i] = True
            tokens[i] = tok.vocab[ids[i]]
            conf[i] = round(0.35 + 0.6 * ((i * 37 + seed) % 100) / 100, 4)
        revealed += len(take)
        frames.append({"step": step, "total_steps": min(steps, len(hole)),
                       "tokens": list(tokens), "committed": list(committed),
                       "conf": list(conf), "just_committed": take, "done": False})
    frames[-1] = {**frames[-1], "done": True, "answer": text[plen:]}
    return text, frames
