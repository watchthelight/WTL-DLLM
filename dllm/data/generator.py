# wtl-dllm · dllm/data/generator.py
# what: seeded procedural math problems, levels 1-5, canonical strings
# why:  every training token comes from here; determinism and clean splits are the contract
# by:   <wtl> watchthelight
# tags: data, generator

import random

SPECIALS = ["[PAD]", "[MASK]", "[BOS]", "[EOS]"]
CHARS = list("0123456789+-*/=x,:")
VOCAB = SPECIALS + CHARS

# canvas length per level (content + [EOS], padded to this with [PAD])
CANVAS = {1: 12, 2: 12, 3: 16, 4: 16, 5: 32}


class MathGen:
    """One seeded stream of problems for one level.

    perturbed=True shifts operand ranges to bands the normal stream never
    touches, so eval_perturbed is disjoint from train by construction,
    not by luck.
    """

    def __init__(self, seed: int, level: int, perturbed: bool = False):
        if level not in CANVAS:
            raise ValueError(f"level {level} not in {sorted(CANVAS)}")
        self.rng = random.Random((seed, level, perturbed).__hash__())
        self.level = level
        self.perturbed = perturbed

    # -- operand bands ---------------------------------------------------
    # train draws operands whose last digit is 0-7; perturbed draws 8-9.
    # crude but airtight: the string sets cannot collide.

    def _num(self, lo: int, hi: int) -> int:
        while True:
            n = self.rng.randint(lo, hi)
            band = n % 10 >= 8
            if band == self.perturbed:
                return n

    # -- levels ----------------------------------------------------------

    def _l1(self) -> str:
        a, b = self._num(0, 99), self._num(0, 99)
        if self.rng.random() < 0.5:
            return f"{a}+{b}={a + b}"
        a, b = max(a, b), min(a, b)
        return f"{a}-{b}={a - b}"

    def _l2(self) -> str:
        a, b = self._num(2, 12), self._num(2, 12)
        if self.rng.random() < 0.5:
            return f"{a}*{b}={a * b}"
        return f"{a * b}/{a}={b}"

    def _l3(self) -> str:
        r = self.rng.random()
        if r < 0.4:
            a, b = self._num(100, 4999), self._num(100, 4999)
            return f"{a}+{b}={a + b}"
        if r < 0.8:
            a, b = self._num(100, 4999), self._num(100, 4999)
            a, b = max(a, b), min(a, b)
            return f"{a}-{b}={a - b}"
        a, b, c = self._num(1, 9), self._num(2, 9), self._num(2, 9)
        return f"{a}+{b}*{c}={a + b * c}"

    def _l4(self) -> str:
        a = self._num(2, 12)
        x = self._num(1, 99)
        b = self._num(1, 99)
        if self.rng.random() < 0.5:
            return f"{a}x+{b}={a * x + b},x={x}"
        c = a * x - b
        if c < 0:
            return self._l4()
        return f"{a}x-{b}={c},x={x}"

    def _l5(self) -> str:
        nums = [self._num(1, 25) for _ in range(self.rng.choice([3, 4]))]
        expr_nums = nums[:]
        self.rng.shuffle(expr_nums)
        expr = str(expr_nums[0])
        val = expr_nums[0]
        for n in expr_nums[1:]:
            op = self.rng.choice("+-*")
            if op == "-" and val - n < 0:
                op = "+"
            expr += op + str(n)
        val = _eval_left_ok(expr)
        if val is None or val > 999:
            return self._l5()
        return f"{','.join(map(str, sorted(nums)))}:{val}={expr}"

    def sample(self) -> str:
        s = getattr(self, f"_l{self.level}")()
        if len(s) + 1 > CANVAS[self.level]:  # +1 for [EOS]
            return self.sample()
        return s


def _eval_left_ok(expr: str):
    """Evaluate with standard precedence; None on any weirdness."""
    try:
        val = eval(expr, {"__builtins__": {}})  # digits and + - * only, made here
        return val if isinstance(val, int) and val >= 0 else None
    except Exception:
        return None


def prompt_len(text: str, level: int) -> int:
    """Chars that stay visible at inference (the question); the rest diffuses.

    L1-L3: through the '='.  L4: through ',x=' (equation given, x wanted).
    L5: through the '=' after the target.
    """
    if level == 4:
        return text.index(",x=") + 3
    return text.index("=") + 1


def check_l5(problem: str) -> bool:
    """`3,7,25:46=25+3*7` — expression uses exactly the given numbers and hits target."""
    given, rest = problem.split(":", 1)
    target, expr = rest.split("=", 1)
    import re
    used = sorted(int(n) for n in re.findall(r"\d+", expr))
    return used == sorted(int(n) for n in given.split(",")) and _eval_left_ok(expr) == int(target)
