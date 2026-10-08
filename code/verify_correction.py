#!/usr/bin/env python3
"""Check that every row of the corrected corpus follows from the original row and its correction record.

    python code/verify_correction.py

For each of the 76,048 rows it rebuilds the corrected option log-probabilities from the original log
(data/responses.jsonl.gz) and the row's `correction` record, recomputes stance, entropy and Likert with the
functions the collection used, and requires exact equality with data/responses_corrected.jsonl.gz:

  native rows   remove the empty-token match (a value shared by three or more options is reset to the -20 floor);
                if the two extremes still tie on a word-label row, split their shared "strongly" mass, giving the
                share `strongly_agree_share` to "strongly agree" and the rest to "strongly disagree";
                rows neither step touches must be unchanged;
  re-drawn rows the probabilities are (c + 0.5) / (n + 2.5) over the categories of the October draws
                (`parsed_counts`); a row with no readable draw gets the collection's neutral fallback.
It also checks the flags themselves: the tie and empty-token flags must be what the original row shows, and
`stance_sign_rule` must be the split given by the sign of p(agree) - p(disagree).
"""
from __future__ import annotations

import gzip
import json
import math
import os
from collections import Counter

import numpy as np

FLOOR = -20.0


# --- functions the collection used (stance, entropy, Likert, and the fallback for an unreadable row) ---
def stance_from_probs(logp):
    p = np.exp(np.asarray(logp)); p /= p.sum()
    idx = np.arange(len(p))
    return float((p * idx).sum() / (len(p) - 1) * 2 - 1)   # [-1,1]


def entropy(logp):
    p = np.exp(np.asarray(logp, dtype=np.float64)); p /= p.sum()
    h = -(p * np.log(np.clip(p, 1e-12, 1))).sum()
    return float(h / math.log(len(p)))           # normalized 0..1


def stance_to_likert(stance):
    return int(np.clip(round((stance + 1.0) / 2.0 * 4.0), 0, 4))


def logprobs_from_stance(stance, sharpness=2.2):
    target = (stance + 1.0) / 2.0 * 4
    idx = np.arange(5, dtype=np.float64)
    logits = -sharpness * np.abs(idx - target)
    logits -= logits.max()
    probs = np.exp(logits)
    probs /= probs.sum()
    return np.log(np.clip(probs, 1e-9, 1.0)).tolist()


# --- the correction ---
def probs(lp):
    p = np.exp(np.asarray(lp, float))
    return p / p.sum()


def remove_empty_token(lp):
    """A non-floor value shared by three or more options is the empty token that matched every label."""
    lp = np.asarray(lp, float).copy()
    cnt = Counter(round(x, 9) for x in lp if x > FLOOR + 0.5)
    shared = [v for v, k in cnt.items() if k >= 3]
    if not shared:
        return lp, False
    for v in shared:
        lp[np.isclose(lp, v, atol=1e-9, rtol=0)] = FLOOR
    return lp, True


def split(p, a):
    p0 = p[0]
    return np.array([(1 - a) * p0, p[1], p[2], p[3], a * p0]) / (1 - p0)


def corrected(orig, corr):
    """(option_logprobs, refused, problems) for one row, from the original row and its correction record."""
    problems = []
    if corr["kind"] == "redrawn":
        if orig["logprob_source"] != "sampling":
            problems.append("re-drawn row was not a sampled row")
        counts = np.array(corr["parsed_counts"], float)
        if counts.sum() == 0:
            return logprobs_from_stance(0.0), True, problems
        return np.log((counts + 0.5) / (counts.sum() + 2.5)).tolist(), False, problems
    if orig["logprob_source"] != "native":
        problems.append("native record on a sampled row")
    lp, empty = remove_empty_token(orig["option_logprobs"])
    p = probs(lp)
    tied = orig["condition_factor"] != "option_labels" and abs(lp[0] - lp[4]) < 1e-12
    if empty != corr["empty_token_removed"] or tied != corr["strongly_tie_repaired"]:
        problems.append("flags do not match the original row")
    if not tied and not empty:
        return orig["option_logprobs"], orig["refused"], problems
    q = p
    if tied:
        q = split(p, corr["strongly_agree_share"])
        a_sign = 1.0 if p[3] > p[1] else (0.0 if p[1] > p[3] else 0.5)
        if stance_from_probs(np.log(np.clip(split(p, a_sign), 1e-9, 1)).tolist()) != corr["stance_sign_rule"]:
            problems.append("stance_sign_rule is not the sign-rule split")
        if corr["share_source"] == "sign_rule" and corr["strongly_agree_share"] != a_sign:
            problems.append("share marked as sign rule differs from the sign rule")
    return np.log(np.clip(q, 1e-9, 1)).tolist(), orig["refused"], problems


def rows(path):
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            yield r["key"], r["value"]


def main():
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    stats, bad = Counter(), []
    for (k0, orig), (k1, new) in zip(rows(os.path.join(here, "responses.jsonl.gz")),
                                     rows(os.path.join(here, "responses_corrected.jsonl.gz"))):
        stats["rows"] += 1
        if k0 != k1:
            bad.append((k1, "row order differs from the original log"))
            continue
        corr = new["correction"]
        lp, refused, problems = corrected(orig, corr)
        s = stance_from_probs(lp)
        ok = (list(lp) == new["option_logprobs"] and refused == new["refused"] and s == new["stance"]
              and entropy(lp) == new["entropy"] and stance_to_likert(s) == new["likert"])
        if not ok:
            problems.append("corrected values do not follow from the original row and its record")
        same = all(new[f] == orig[f] for f in orig if f not in ("stance", "likert", "entropy", "option_logprobs", "refused"))
        if not same:
            problems.append("a field the correction does not touch has changed")
        for p in problems:
            bad.append((k1, p))
        stats[corr["kind"] + (" (split measured)" if corr.get("share_source") == "measured" else "")] += 1
        stats["changed"] += new["stance"] != orig["stance"]
    print(dict(stats))
    print(f"{stats['rows'] - len({k for k, _ in bad}):,} of {stats['rows']:,} rows verified")
    for k, p in bad[:10]:
        print("  FAIL", k[:12], p)
    raise SystemExit(0 if not bad and stats["rows"] == 76048 else 1)


if __name__ == "__main__":
    main()
