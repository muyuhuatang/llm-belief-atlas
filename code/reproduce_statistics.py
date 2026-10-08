#!/usr/bin/env python3
"""Reproduce the statistics printed in the two-page summary from a corpus file.

    python code/reproduce_statistics.py                                    # corrected corpus (arXiv version)
    python code/reproduce_statistics.py --corpus data/responses.jsonl.gz   # original log (VIS poster version)
    python code/reproduce_statistics.py --sign-rule                        # sensitivity: sign rule on every tied row
    python code/reproduce_statistics.py --out results.json                 # also write every value to a file

Run from the repository root. It takes about five minutes on a laptop, mostly the bootstrap (1,000 resamples)
and the no-mechanism null (20 draws, plus 20 for the split-half control). Seeds are fixed, so every run prints the
same numbers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import belief_stats as BS  # noqa: E402

SHORT = {"meta-llama/llama-3.3-70b-instruct": "Llama-3.3-70B", "qwen/qwen-2.5-72b-instruct": "Qwen-2.5-72B",
         "deepseek/deepseek-chat": "DeepSeek-V3", "gpt-4o-mini": "GPT-4o-mini"}


def likert(s):
    return int(np.clip(round((s + 1.0) / 2.0 * 4.0), 0, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.join("data", "responses_corrected.jsonl.gz"))
    ap.add_argument("--sign-rule", action="store_true",
                    help="corrected corpus only: split every tied row by the sign rule instead of the measured share")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rows = BS.load_rows(args.corpus)
    if args.sign_rule:
        rows = [dict(r, stance=r["correction"]["stance_sign_rule"])
                if r.get("correction", {}).get("strongly_tie_repaired") else r for r in rows]
    models = sorted({r["model"] for r in rows})
    print(f"{args.corpus}: {len(rows):,} rows{' (sign rule on tied rows)' if args.sign_rule else ''}\n")
    res = {"corpus": os.path.basename(args.corpus), "sign_rule": args.sign_rule}

    for key, ms, name in (("all_models", models, "all four models"), ("native_models", BS.NATIVE_MODELS, "the two natively-read models")):
        part = BS.partition(rows, ms)
        ci = BS.bootstrap_ci(rows, ms)
        res[key] = {"partition": part, "bootstrap_ci95": ci}
        p, d = part["partition_pct"], part["dims"]
        print(f"Variance split, {name} ({d['models']} x {d['items']} x {d['conditions']} = {d['models'] * d['items'] * d['conditions']:,} cells)")
        for k in ("belief", "condition", "residual"):
            print(f"  {k:10s} {p[k]:6.2f}%   95% CI [{ci[k][0]:.2f}, {ci[k][1]:.2f}]")
        print("  components: " + ", ".join(f"{k} {v:.2f}" for k, v in part["components_pct"].items()) + "\n")

    g = BS.gating(rows)
    null, null_sh = BS.gating_null(rows), BS.gating_null(rows, split_half=True)
    res["gating"] = {"observed": g, "no_mechanism_null": null, "no_mechanism_null_split_half": null_sh}
    print(f"Reliability gating, {g['n_models']} models, {g['n_items']} propositions")
    print(f"  Spearman rho(inconsistency, W) {g['rho']:+.4f}   permutation p {g['perm_p']:.4f}")
    print(f"  no-mechanism null              {null['mean']:+.4f} +/- {null['sd']:.4f}   (z {(null['mean'] - g['rho']) / null['sd']:.1f})")
    print(f"  split-half control             {g['split_half_rho_mean']:+.4f}   null {null_sh['mean']:+.4f} +/- {null_sh['sd']:.4f}\n")

    ce = BS.condition_effects(rows)
    res["condition_effects"] = ce
    pd = ce["pressure_signed_delta"]
    print("Mean shift from the default stance under user pressure")
    for k in ("disagree_push", "agree_push", "authority", "repeat_challenge"):
        print(f"  {k:17s} {pd[k]:+.3f}")
    print("Mean |shift| from the default stance, by condition family")
    for f, v, n in ce["effect_by_factor"]:
        print(f"  {f:14s} {v:.3f}   ({n:,} rows)")

    by = {(r["model"], r["item_id"], r["condition_key"]): r for r in rows}
    res["table1"] = {}
    print("\nTable 1: pol.006 (\"Generous welfare programs reduce people's incentive to seek employment\"), default condition")
    for m in models:
        r = by[(m, "pol.006", "default")]
        res["table1"][m] = {"likert": likert(r["stance"]), "stance": r["stance"], "entropy": r["entropy"]}
        print(f"  {SHORT[m]:14s} Likert {likert(r['stance'])}   s {round(r['stance'], 2) + 0.0:+.2f}   H {r['entropy']:.2f}")
    llama = BS.NATIVE_MODELS[1]
    sweden = next(k for (m, it, k) in by if m == llama and it == "pol.006" and "Sweden" in k)
    res["llama_pol006_sweden_stance"] = by[(llama, "pol.006", sweden)]["stance"]
    print(f"  Llama-3.3-70B under the Sweden persona: s {res['llama_pol006_sweden_stance']:+.2f}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
