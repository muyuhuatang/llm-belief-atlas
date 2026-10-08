#!/usr/bin/env python3
"""Test the answer parser on every label scheme the 49 conditions present, and show where the original one fails.

    python code/test_answer_parser.py

Six schemes cover all 49 conditions: the five word labels in order (44 conditions), reversed, shuffled, numbers
1-5, flipped numbers (1 = strongly agree), and letters A-E. Each scheme is tested with each of the five answers in
six forms. The corrected parser must read every case; the original parser must fail the known ones, or the test
would not be able to tell the two apart.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from answer_parser import LIKERT_OPTIONS, original_parse, parse  # noqa: E402

SCHEMES = {
    "word labels, in order": [("strongly disagree", 0), ("disagree", 1), ("neither agree nor disagree", 2), ("agree", 3), ("strongly agree", 4)],
    "option_order=reversed": [("strongly agree", 4), ("agree", 3), ("neither agree nor disagree", 2), ("disagree", 1), ("strongly disagree", 0)],
    "option_order=shuffled": [("neither agree nor disagree", 2), ("agree", 3), ("strongly agree", 4), ("strongly disagree", 0), ("disagree", 1)],
    "option_labels=numeric": [("1", 0), ("2", 1), ("3", 2), ("4", 3), ("5", 4)],
    "option_labels=flipped_numeric": [("5", 0), ("4", 1), ("3", 2), ("2", 3), ("1", 4)],
    "option_labels=letters": [("A", 0), ("B", 1), ("C", 2), ("D", 3), ("E", 4)],
}


def cases(l2c):
    inv = {c: lab for lab, c in l2c.items()}
    for c in range(5):
        lab, opt = inv[c], LIKERT_OPTIONS[c]
        for ans in (lab, f"{lab} = {opt}", f"{lab}.", f"**{lab}**", opt, f"I {opt} with this."):
            yield c, ans


def main():
    n = fails = orig_fails = 0
    examples = []
    for name, pairs in SCHEMES.items():
        l2c = dict(pairs)
        for c, ans in cases(l2c):
            n += 1
            if parse(ans, l2c) != c:
                fails += 1
                print(f"FAIL {name}: {ans!r} -> {parse(ans, l2c)} (expected {c})")
            o = original_parse(ans, l2c)
            if o != c:
                orig_fails += 1
                if len(examples) < 6:
                    examples.append(f"{name}: {ans!r} read as {o}, should be {c}")
    words = dict(SCHEMES["word labels, in order"])
    known = original_parse("strongly agree", words) == 3 and original_parse("neither agree nor disagree", words) == 1
    print(f"{n} cases; corrected parser failures: {fails}; original parser failures: {orig_fails}, for example:")
    for e in examples:
        print("  " + e)
    print(f"original parser reads 'strongly agree' as agree and 'neither agree nor disagree' as disagree: {known}")
    ok = fails == 0 and orig_fails > 0 and known
    print("PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
