# wtl-dllm · dllm/model/tokenizer.py
# what: char-level tokenizer over the datagen vocab; digits atomic
# by:   <wtl> watchthelight
# tags: model, tokenizer

import json
from pathlib import Path

from dllm.data.generator import VOCAB


class Tokenizer:
    def __init__(self, vocab: list[str] | None = None):
        self.vocab = list(vocab) if vocab else list(VOCAB)
        self.t2i = {t: i for i, t in enumerate(self.vocab)}

    @classmethod
    def from_file(cls, path: str | Path) -> "Tokenizer":
        return cls(json.loads(Path(path).read_text()))

    @property
    def pad_id(self) -> int: return self.t2i["[PAD]"]
    @property
    def mask_id(self) -> int: return self.t2i["[MASK]"]
    @property
    def eos_id(self) -> int: return self.t2i["[EOS]"]

    def __len__(self) -> int:
        return len(self.vocab)

    def encode(self, text: str, canvas: int | None = None) -> list[int]:
        ids = [self.t2i[c] for c in text]
        if canvas is not None:
            if len(ids) + 1 > canvas:
                raise ValueError(f"{text!r} too long for canvas {canvas}")
            ids = ids + [self.eos_id] + [self.pad_id] * (canvas - len(ids) - 1)
        return ids

    def decode(self, ids) -> str:
        out = []
        for i in ids:
            tok = self.vocab[int(i)]
            if tok == "[EOS]":
                break
            out.append("" if tok in ("[PAD]", "[MASK]") else tok)
        return "".join(out)

    def decode_raw(self, ids) -> list[str]:
        """No EOS cut, specials kept — what the ui frame wants."""
        return [self.vocab[int(i)] for i in ids]
