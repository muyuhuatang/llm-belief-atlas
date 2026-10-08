#!/usr/bin/env python3
"""Convergence of the three readouts, and their method-specific variance, on the 1,552-cell subset.

    python code/three_channel_subset.py              # corrected channels (arXiv version)
    python code/three_channel_subset.py --original   # the channels as first read (VIS poster version)
    python code/three_channel_subset.py --sign-rule  # sensitivity: sign rule on every tied native cell

The subset (data/three_channel_subset.jsonl) holds every model and proposition at the default condition, with
three independent readouts per cell: a separately asked agreement rating, the option log-probability stance, and
the written justification projected onto the proposition's agree-minus-disagree axis. This script computes the
correlations between them, overall and per model, and the one-common-factor decomposition: with three channels the
model is just-identified, and channel i's shared variance is r_ij * r_ik / r_jk; the rest is method-specific.
The correlations are rounded to three decimals before the decomposition, as in the original analysis.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

NATIVE = {"meta-llama/llama-3.3-70b-instruct", "gpt-4o-mini"}
NAMES = ["agreement", "logprob", "reflection"]


def corr(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(np.corrcoef(a, b)[0, 1]) if a.std() > 1e-9 and b.std() > 1e-9 else float("nan")


def summary(agreement, logprob, reflection, models):
    agreement, logprob, reflection = np.array(agreement), np.array(logprob), np.array(reflection)
    n = len(agreement)
    chans = {"agreement": agreement, "logprob": logprob, "reflection": reflection}
    M = np.array([[corr(chans[a], chans[b]) for b in NAMES] for a in NAMES])
    permodel = {}
    for m in sorted(set(models)):
        idx = [k for k in range(n) if models[k] == m]
        ag, lp, rf = agreement[idx], logprob[idx], reflection[idx]
        permodel[m] = {"agree_logprob": round(corr(ag, lp), 3), "agree_reflection": round(corr(ag, rf), 3),
                       "logprob_reflection": round(corr(lp, rf), 3), "n": len(idx)}
    sg = np.vstack([np.sign(agreement), np.sign(logprob), np.sign(reflection)])
    all_agree = np.mean(np.all(sg == sg[0], axis=0))
    return {"n": n, "correlations": {NAMES[i]: {NAMES[j]: round(float(M[i, j]), 3) for j in range(3)} for i in range(3)},
            "by_model": permodel, "three_channel_sign_agreement_pct": round(100 * all_agree, 1)}


def method_variance(s):
    M = s["correlations"]
    r_al, r_ar, r_lr = M["agreement"]["logprob"], M["agreement"]["reflection"], M["logprob"]["reflection"]
    comm = {"agreement": (r_al * r_ar) / r_lr, "logprob": (r_al * r_lr) / r_ar, "reflection": (r_ar * r_lr) / r_al}
    return {"convergent_mean_offdiag": round((r_al + r_ar + r_lr) / 3, 3),
            "shared_variance_pct": {k: round(100 * comm[k], 1) for k in comm},
            "method_specific_variance_pct": {k: round(100 * (1 - comm[k]), 1) for k in comm}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", default=os.path.join("data", "three_channel_subset.jsonl"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--original", action="store_true")
    g.add_argument("--sign-rule", action="store_true")
    args = ap.parse_args()
    cells = [json.loads(l) for l in open(args.subset)]
    if args.original:
        ag = [c["original"]["agreement"] for c in cells]
        lp = [c["original"]["logprob_stance"] for c in cells]
    else:
        ag = [c["agreement"] for c in cells]
        lp = [c["correction"]["stance_sign_rule"] if args.sign_rule and c["correction"].get("strongly_tie_repaired")
              else c["logprob_stance"] for c in cells]
    s = summary(ag, lp, [c["reflection"] for c in cells], [c["model"] for c in cells])
    mv = method_variance(s)
    print(f"{len(cells):,} cells{' (original readouts)' if args.original else ' (sign rule on tied cells)' if args.sign_rule else ''}")
    print("correlations: " + ", ".join(f"{a}~{b} {s['correlations'][a][b]:.3f}" for a, b in
                                        (("agreement", "logprob"), ("agreement", "reflection"), ("logprob", "reflection"))))
    for m, v in s["by_model"].items():
        tag = "native" if m in NATIVE else "sampled"
        print(f"  {m:36s} agree~logprob {v['agree_logprob']:.3f}  agree~reflection {v['agree_reflection']:.3f}  "
              f"logprob~reflection {v['logprob_reflection']:.3f}  [{tag} logprob]")
    print(f"three channels share the stance sign on {s['three_channel_sign_agreement_pct']}% of cells")
    print("method-specific variance: " + ", ".join(f"{k} {v}%" for k, v in mv["method_specific_variance_pct"].items()))
    print(f"mean convergent correlation {mv['convergent_mean_offdiag']}")


if __name__ == "__main__":
    main()
