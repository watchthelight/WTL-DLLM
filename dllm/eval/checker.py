# wtl-dllm · dllm/eval/checker.py
# what: grade one generated answer against its problem — correct / wrong / malformed
# why:  the model never grades itself; this is the external verifier
# by:   <wtl> watchthelight
# tags: eval, checker

import re

from dllm.data.generator import _eval_left_ok, prompt_len


def grade(problem: str, generated_answer: str, level: int) -> str:
    """problem: full reference row text. generated_answer: model text after the prompt
    (already EOS-cut). Returns 'correct' | 'wrong' | 'malformed'."""
    ref_answer = problem[prompt_len(problem, level):]

    if level in (1, 2, 3):
        if not re.fullmatch(r"\d+", generated_answer):
            return "malformed"
        left = problem[: problem.rindex("=")]
        truth = _eval_left_ok(left)
        return "correct" if int(generated_answer) == truth else "wrong"

    if level == 4:
        if not re.fullmatch(r"\d+", generated_answer):
            return "malformed"
        return "correct" if int(generated_answer) == int(ref_answer) else "wrong"

    if level == 5:
        # any expression that uses exactly the given numbers and hits the target counts
        if not re.fullmatch(r"[\d+\-*]+", generated_answer):
            return "malformed"
        given, rest = problem.split(":", 1)
        target = int(rest.split("=", 1)[0])
        used = sorted(int(n) for n in re.findall(r"\d+", generated_answer))
        if used != sorted(int(n) for n in given.split(",")):
            return "wrong"
        return "correct" if _eval_left_ok(generated_answer) == target else "wrong"

    raise ValueError(f"level {level}")
