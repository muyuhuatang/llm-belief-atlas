# `data/atlas/` — the reflection layout

One binary file and a manifest.

```
manifest.json          the labels, the counts, the format
pos_reflection.bin     76,048 x 2 float32 — the only layout that cannot be recomputed
```

This folder used to hold eight arrays. Seven of them were a convenience cache: they rebuild exactly
from `../responses.jsonl.gz`, so they were removed rather than shipped twice. The recipe that
regenerates them is at the bottom of this file, and it is tested — five come back **bit-for-bit
identical**, the two remaining layouts to `float32` rounding.

**`pos_reflection.bin` is the exception, and that is why it is here.** It is a 2-D projection of an
OpenAI sentence embedding of each `justification`, and the embedding is not in this release. Nobody
can regenerate this file from these bytes. Everything else can.

---

## `pos_reflection.bin`

`float32`, little-endian, no header, no padding: 76,048 records of `(x, y)` = 608,384 bytes.
**Row *i* is line *i* of `../responses.jsonl.gz`** — that index correspondence is what makes the
whole thing work, and it holds across the full corpus.

```python
import json, numpy as np

m  = json.load(open("data/atlas/manifest.json"))
xy = np.fromfile("data/atlas/pos_reflection.bin", "<f4").reshape(-1, 2)   # (76048, 2)

topics = m["attributes"]["domain"]["labels"]     # ['ethics', 'politics', ... ]
models = m["attributes"]["model"]["labels"]      # ['meta-llama/llama-3.3-70b-instruct', ... ]
```

Coordinates are normalised into `[-1, 1]` with 4% padding, so every value lies within **+/-0.96**.
Distance in this layout is roughly similarity of wording: the model's own justifications, embedded,
then projected with PCA. This is the layout with real structure — topics form soft lobes — and it is
what panel 1 of the poster plots.

### `bounds` in the manifest is not the extent of this file

It records the extent of each layout *before* the final normalisation — the inverse-transform record,
kept so the original scale can be recovered. Do not set a camera from it. Compute the extent instead:

```python
p = np.fromfile("data/atlas/pos_reflection.bin", "<f4").reshape(-1, 2)
xmin, ymin = p.min(0); xmax, ymax = p.max(0)     # -0.96 -0.857 0.96 0.857
```

(The mismatch is inherited from the pipeline that produced the corpus; the values here are
unmodified, so they match the project's own files rather than being silently corrected.)

### `source: "elicited"`

Means these coordinates come from the real corpus. Worth checking, because the project also produced
point clouds in this identical format from synthetic data, and those carry `source: "synthetic"`.
None of them is in this release, but if you meet a manifest of this shape from elsewhere, that field
is what tells the two apart.

---

## What the derived arrays are

The recipe below writes seven files. What they mean:

| array | dtype | meaning |
|---|---|---|
| `attr_stance` | `float32` | -1 disagrees ... +1 agrees; the expected value over the five option probabilities |
| `attr_uncertainty` | `float32` | entropy of those same five probabilities, 0 certain ... ~1 flat |
| `attr_inconsistency` | `float32` | how much the whole option distribution moves across phrasings |
| `attr_model`, `attr_domain` | `uint8` | index into the label lists in `manifest.json` |
| `pos_logprob` | `float32` | 76,048 x 2 — the option-probability layout |
| `pos_agreement` | `float32` | 76,048 x 2 — the agreement layout |

**`attr_inconsistency` is not a per-row value.** It is a generalized Jensen-Shannon divergence over
the per-condition option distributions, computed per (model, proposition) — 1,552 cells — over
**47 of the 49 conditions**, since the two `polarity` conditions are excluded because negating a
proposition is supposed to flip the answer. The cell value is then repeated across all 49 of its
rows, which is why a 76,048-row array holds only 1,485 distinct values. You have 1,552 independent
numbers here, not 76,048, and any test that assumes otherwise will overstate its own significance.

**`pos_agreement` is near-degenerate.** 96.79% of its variance sits on a single component, because
the two coordinates it is built from are the option-derived stance and a rounding of that same
stance. No poster panel reads it — panel 3 is a constructed stance-by-topic layout built from
`attr_stance` and `attr_domain` instead.

**`pos_logprob` carries stance as a direction, not a clean gradient.** A linear fit of stance on its
two coordinates gives R2 = 0.33, so a third of the variation lines up with position and two thirds
does not.

### Read direction, not distance

Each layout is normalised to its own bounding box after alignment, so the uniform scale that
Procrustes fitted is overwritten. A point moving between layouts tells you the *direction* and
*relative* displacement of a disagreement between readouts. **The magnitude is not on a common scale
and should not be read as one.** The measured correspondence between channels is above chance but
small — 6.1-11.8% shared structure.

---

## The rebuild recipe

Save this as `rebuild_atlas.py` at the repository root and run it.

```python
"""Rebuild every derived atlas array from responses.jsonl.gz + pos_reflection.bin."""
import gzip, json
import numpy as np

K = 5  # answer options

def load_rows(path="data/responses.jsonl.gz"):
    with gzip.open(path, "rt") as f:
        return [json.loads(line)["value"] for line in f]

def _dist(lp):
    p = np.exp(np.asarray(lp, float))
    return p / p.sum()

def _entropy(p):
    p = np.clip(p, 1e-12, 1.0)
    return float(-(p * np.log(p)).sum())

def _pca2(X):
    Xc = np.asarray(X, float) - np.asarray(X, float).mean(0)
    _, _, vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ vt[:2].T

def _procrustes(target, source):
    t, s = np.asarray(target, float), np.asarray(source, float)
    tc, sc = t.mean(0), s.mean(0)
    t0, s0 = t - tc, s - sc
    u, _, vt = np.linalg.svd(s0.T @ t0)
    R = u @ vt
    scale = np.trace((s0 @ R).T @ t0) / np.trace(s0.T @ s0)
    return (s0 @ R) * scale + tc

def _normalize(P, pad=0.04):
    P = np.asarray(P, float)
    mn, mx = P.min(0), P.max(0)
    span = (mx - mn).max()
    return ((P - (mn + mx) / 2) / (span / 2) * (1 - pad)).astype(np.float32)

def rebuild(rows, manifest, reflection):
    """reflection = the shipped pos_reflection.bin, (76048, 2) float32."""
    ml = manifest["attributes"]["model"]["labels"]
    dl = manifest["attributes"]["domain"]["labels"]
    out = {
        "attr_stance":      np.array([r["stance"]  for r in rows], np.float32),
        "attr_uncertainty": np.array([r["entropy"] for r in rows], np.float32),
        "attr_model":       np.array([ml.index(r["model"])  for r in rows], np.uint8),
        "attr_domain":      np.array([dl.index(r["domain"]) for r in rows], np.uint8),
    }
    # inconsistency: generalized Jensen-Shannon divergence of the per-condition option
    # distributions, per (model, item), over the 47 non-polarity conditions, / log K.
    groups = {}
    for r in rows:
        if r["condition_factor"] == "polarity":
            continue
        groups.setdefault((r["model"], r["item_id"]), []).append(_dist(r["option_logprobs"]))
    jsd = {}
    for key, D in groups.items():
        if len(D) < 2:
            jsd[key] = 0.0
            continue
        D = np.stack(D)
        gen = _entropy(D.mean(0)) - float(np.mean([_entropy(d) for d in D]))
        jsd[key] = max(0.0, min(1.0, gen / np.log(K)))
    out["attr_inconsistency"] = np.array(
        [jsd.get((r["model"], r["item_id"]), 0.0) for r in rows], np.float32)

    # the other two layouts: project, align onto the reflection anchor, rescale to [-1, 1]
    logprob   = np.array([r["option_logprobs"] for r in rows], float)
    agreement = np.column_stack([[r["stance"] for r in rows],
                                 [r["likert"] / 4 * 2 - 1 for r in rows]])
    out["pos_logprob"]   = _normalize(_procrustes(reflection, _pca2(logprob)))
    out["pos_agreement"] = _normalize(_procrustes(reflection, agreement))
    return out

if __name__ == "__main__":
    rows       = load_rows()
    manifest   = json.load(open("data/atlas/manifest.json"))
    reflection = np.fromfile("data/atlas/pos_reflection.bin", "<f4").reshape(-1, 2)
    for name, arr in rebuild(rows, manifest, reflection).items():
        arr.tofile(f"data/atlas/{name}.bin")
        print(f"wrote data/atlas/{name}.bin  {arr.shape} {arr.dtype}")
```

Most of the runtime is parsing the 11 MB log. Verified against the arrays that used to ship here:
`attr_stance`, `attr_uncertainty`, `attr_inconsistency`, `attr_model` and `attr_domain` come back
**bit-for-bit identical**; `pos_logprob` and `pos_agreement` agree to 1.8e-07 and 1.2e-07, which is
`float32` rounding in the Procrustes step.

---

## Before you use `attr_stance`

It carries a known defect. A matcher that collides on shared words records answers as neutral even
where the model's own `justification` is decisive. The signature is
`option_logprobs[0] == option_logprobs[4] == max(option_logprobs)`, and it marks **18,420 of the
75,867 non-refused rows (24.3%)**; 77.8% of those open with an explicit "agree" or "disagree". Two
published findings were withdrawn because of it.

**Do not recompute from `option_logprobs` — that is where the defect lives.** The stored vector is
the matcher's own output: in 69,129 of 76,048 rows (90.9%) it carries the identical log-probability
for the two opposite extremes, and reconstructing a stance from it returns the same wrong number.
Only the `justification` text escaped it. Worked example in the
[top-level README](../../README.md#two-bugs-we-found-in-our-own-code).

## Before you use `attr_uncertainty`

It mixes two estimators. For 51.1% of rows the option probabilities were estimated from up to three
samples rather than read natively, and the sampled estimator has a hard entropy floor the native one
does not. The split is almost entirely determined by model identity — Qwen and DeepSeek are wholly
sampled, GPT-4o-mini wholly native, and only Llama-3.3-70B is mixed (18,142 native, 870 sampled) — so
comparing uncertainty across models largely compares two different measurement procedures. See
[`../README.md`](../README.md#half-the-probabilities-are-estimates).

Licensed CC BY 4.0 — see [LICENSE](../../LICENSE).
