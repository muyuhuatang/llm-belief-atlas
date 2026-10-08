"""The statistics behind the LLM Belief Atlas summary, as functions over a corpus file in ../data/.

The variance decomposition, its item bootstrap and the reliability-gating test are copied without change from
the analysis scripts that produced the poster's numbers. The no-mechanism null and the condition-effect summary
are written out here as functions. reproduce_statistics.py applies all of them to a corpus.
"""
from __future__ import annotations

import gzip
import json
from collections import defaultdict

import numpy as np

NATIVE_MODELS = ["gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct"]   # sorted, as the analysis sorts them


def load_rows(path):
    """All rows of a corpus file, in file order, each with its cache key."""
    by_key = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                by_key[r["key"]] = dict(r["value"], key=r["key"])
    return list(by_key.values())


# --------------------------------------------------------------------------- variance decomposition
def build_cube(cells, models):
    """Return (S[a,b,c] stance cube, items, conds) for the given model subset; require completeness."""
    mset = set(models)
    sub = [c for c in cells if c["model"] in mset]
    items = sorted({c["item_id"] for c in sub})
    conds = sorted({c["condition_key"] for c in sub})
    mi = {m: i for i, m in enumerate(models)}
    xi = {x: i for i, x in enumerate(items)}
    ci = {c: i for i, c in enumerate(conds)}
    a, b, cc = len(models), len(items), len(conds)
    S = np.full((a, b, cc), np.nan, np.float64)
    for c in sub:
        S[mi[c["model"]], xi[c["item_id"]], ci[c["condition_key"]]] = c["stance"]
    return S, items, conds


def gtheory_3way(S):
    """Random-effects variance components for a balanced single-replicate A x B x C design."""
    a, b, c = S.shape
    g = S.mean()
    Am = S.mean(axis=(1, 2)); Bm = S.mean(axis=(0, 2)); Cm = S.mean(axis=(0, 1))
    ABm = S.mean(axis=2); ACm = S.mean(axis=1); BCm = S.mean(axis=0)
    SS_t = ((S - g) ** 2).sum()
    SS_A = b * c * ((Am - g) ** 2).sum()
    SS_B = a * c * ((Bm - g) ** 2).sum()
    SS_C = a * b * ((Cm - g) ** 2).sum()
    SS_AB = c * ((ABm - Am[:, None] - Bm[None, :] + g) ** 2).sum()
    SS_AC = b * ((ACm - Am[:, None] - Cm[None, :] + g) ** 2).sum()
    SS_BC = a * ((BCm - Bm[:, None] - Cm[None, :] + g) ** 2).sum()
    SS_ABC = SS_t - (SS_A + SS_B + SS_C + SS_AB + SS_AC + SS_BC)
    df = {"A": a - 1, "B": b - 1, "C": c - 1, "AB": (a - 1) * (b - 1),
          "AC": (a - 1) * (c - 1), "BC": (b - 1) * (c - 1), "ABC": (a - 1) * (b - 1) * (c - 1)}
    MS = {"A": SS_A / df["A"], "B": SS_B / df["B"], "C": SS_C / df["C"], "AB": SS_AB / df["AB"],
          "AC": SS_AC / df["AC"], "BC": SS_BC / df["BC"], "ABC": SS_ABC / df["ABC"]}
    v = {}
    v["ABC"] = MS["ABC"]
    v["AB"] = (MS["AB"] - MS["ABC"]) / c
    v["AC"] = (MS["AC"] - MS["ABC"]) / b
    v["BC"] = (MS["BC"] - MS["ABC"]) / a
    v["A"] = (MS["A"] - MS["AB"] - MS["AC"] + MS["ABC"]) / (b * c)
    v["B"] = (MS["B"] - MS["AB"] - MS["BC"] + MS["ABC"]) / (a * c)
    v["C"] = (MS["C"] - MS["AC"] - MS["BC"] + MS["ABC"]) / (a * b)
    return v, MS, df


LABEL = {"A": "Model (M)", "B": "Item (X)", "C": "Condition (C)", "AB": "Model x Item (M x X)",
         "AC": "Model x Condition (M x C)", "BC": "Item x Condition (X x C)", "ABC": "Residual (M x X x C + noise)"}


def partition(rows, models):
    """Seven variance components (negatives clamped to 0, as in standard G-theory), and their collapse into
    belief = M + X + MxX, condition = C + MxC + XxC, residual = MxXxC. The collapse is a grouping rule we chose."""
    S, items, conds = build_cube(rows, models)
    if np.isnan(S).any():
        raise ValueError(f"cube not complete: {int(np.isnan(S).sum())} missing cells")
    v, _, _ = gtheory_3way(S)
    vc = {k: max(0.0, val) for k, val in v.items()}
    tot = sum(vc.values())
    pct = {k: 100 * val / tot for k, val in vc.items()}
    return {"dims": {"models": S.shape[0], "items": S.shape[1], "conditions": S.shape[2]},
            "components_pct": {LABEL[k]: pct[k] for k in LABEL},
            "partition_pct": {"belief": pct["A"] + pct["B"] + pct["AB"],
                              "condition": pct["C"] + pct["AC"] + pct["BC"],
                              "residual": pct["ABC"]}}


# --------------------------------------------------------------------------- item bootstrap
def gtheory_partition(S):
    """Return (belief%, condition%, residual%) for a balanced A x B x C single-replicate design."""
    a, b, c = S.shape
    g = S.mean()
    Am = S.mean(axis=(1, 2)); Bm = S.mean(axis=(0, 2)); Cm = S.mean(axis=(0, 1))
    ABm = S.mean(axis=2); ACm = S.mean(axis=1); BCm = S.mean(axis=0)
    SS_t = ((S - g) ** 2).sum()
    SS_A = b * c * ((Am - g) ** 2).sum(); SS_B = a * c * ((Bm - g) ** 2).sum(); SS_C = a * b * ((Cm - g) ** 2).sum()
    SS_AB = c * ((ABm - Am[:, None] - Bm[None, :] + g) ** 2).sum()
    SS_AC = b * ((ACm - Am[:, None] - Cm[None, :] + g) ** 2).sum()
    SS_BC = a * ((BCm - Bm[:, None] - Cm[None, :] + g) ** 2).sum()
    SS_ABC = SS_t - (SS_A + SS_B + SS_C + SS_AB + SS_AC + SS_BC)
    MS = {"A": SS_A/(a-1), "B": SS_B/(b-1), "C": SS_C/(c-1), "AB": SS_AB/((a-1)*(b-1)),
          "AC": SS_AC/((a-1)*(c-1)), "BC": SS_BC/((b-1)*(c-1)), "ABC": SS_ABC/((a-1)*(b-1)*(c-1))}
    v = {"ABC": MS["ABC"], "AB": (MS["AB"]-MS["ABC"])/c, "AC": (MS["AC"]-MS["ABC"])/b, "BC": (MS["BC"]-MS["ABC"])/a,
         "A": (MS["A"]-MS["AB"]-MS["AC"]+MS["ABC"])/(b*c), "B": (MS["B"]-MS["AB"]-MS["BC"]+MS["ABC"])/(a*c),
         "C": (MS["C"]-MS["AC"]-MS["BC"]+MS["ABC"])/(a*b)}
    vc = {k: max(0.0, val) for k, val in v.items()}
    tot = sum(vc.values()) or 1e-12
    belief = 100*(vc["A"]+vc["B"]+vc["AB"])/tot
    cond = 100*(vc["C"]+vc["AC"]+vc["BC"])/tot
    resid = 100*vc["ABC"]/tot
    return belief, cond, resid


def cube_for(cells, models, items):
    mset, iset = set(models), set(items)
    conds = sorted({c["condition_key"] for c in cells if c["model"] in mset})
    mi = {m: i for i, m in enumerate(models)}; ci = {c: i for i, c in enumerate(conds)}
    xi = {x: i for i, x in enumerate(items)}
    S = np.full((len(models), len(items), len(conds)), np.nan)
    for c in cells:
        if c["model"] in mset and c["item_id"] in iset:
            S[mi[c["model"]], xi[c["item_id"]], ci[c["condition_key"]]] = c["stance"]
    return S, conds


def bootstrap_ci(rows, models, B=1000, seed=0):
    """Resample propositions with replacement; 2.5 / 97.5 percentiles of the three shares."""
    items = sorted({c["item_id"] for c in rows if c["model"] in set(models)})
    S, _ = cube_for(rows, models, items)
    rng = np.random.default_rng(seed)
    idx = np.arange(len(items))
    boots = np.array([gtheory_partition(S[:, rng.choice(idx, size=len(idx), replace=True), :]) for _ in range(B)])
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    lab = ["belief", "condition", "residual"]
    return {lab[i]: [float(lo[i]), float(hi[i])] for i in range(3)}


# --------------------------------------------------------------------------- reliability gating
def avg_ranks(x):
    """Average ranks (1..n) of x, ties averaged."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0  # mean of ranks (i+1..j+1)
        i = j + 1
    return ranks


def kendalls_w(data):
    """Kendall's W for data shaped (m_judges, n_objects), with tie correction."""
    m, n = data.shape
    if m < 2 or n < 2:
        return np.nan
    R = np.zeros((m, n))
    Tcorr = 0.0
    for i in range(m):
        R[i] = avg_ranks(data[i])
        _, counts = np.unique(data[i], return_counts=True)
        Tcorr += float(np.sum(counts ** 3 - counts))
    Rj = R.sum(axis=0)
    S = float(np.sum((Rj - Rj.mean()) ** 2))
    denom = m ** 2 * (n ** 3 - n) - m * Tcorr
    return 12.0 * S / denom if denom > 0 else np.nan


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    rx, ry = avg_ranks(x), avg_ranks(y)
    if rx.std() < 1e-12 or ry.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def perm_p(x, y, obs, B=5000, seed=0):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float)
    cnt = 0
    for _ in range(B):
        if abs(spearman(x, rng.permutation(y))) >= abs(obs) - 1e-12:
            cnt += 1
    return (cnt + 1) / (B + 1)


def _gating_table(rows):
    table = defaultdict(lambda: defaultdict(dict))
    for c in rows:
        if c["condition_factor"] == "polarity":           # negation is meant to flip the answer
            continue
        table[c["item_id"]][c["model"]][c["condition_key"]] = c["stance"]
    return table


def gating(rows, perm_B=5000, n_splits=20, seed=0):
    """Per proposition: inconsistency = mean over models of the SD of its stance across conditions; W = Kendall's W
    of the cross-model ordering, with conditions as judges. Returns Spearman rho(inconsistency, W), a permutation p
    against rho = 0, and the disjoint split-half control (inconsistency from one half of the conditions, W from the
    other)."""
    models = sorted({c["model"] for c in rows})
    table = _gating_table(rows)
    incons, W = [], []
    for it in sorted(table):
        md = table[it]
        if len(md) < len(models):
            continue
        conds = sorted(set.intersection(*[set(md[m]) for m in models]))
        if len(conds) < 3:
            continue
        mat = np.array([[md[m][k] for m in models] for k in conds])
        W.append(kendalls_w(mat))
        incons.append(float(np.mean([np.std([md[m][k] for k in conds]) for m in models])))
    incons, W = np.array(incons), np.array(W)
    ok = ~np.isnan(W)
    incons, W = incons[ok], W[ok]
    r = spearman(incons, W)
    p = perm_p(incons, W, r, B=perm_B) if perm_B else None
    rng = np.random.default_rng(seed)
    split_rs = []
    for _ in range(n_splits):
        inc_h, W_h = [], []
        for it in sorted(table):
            md = table[it]
            if len(md) < len(models):
                continue
            conds = sorted(set.intersection(*[set(md[m]) for m in models]))
            if len(conds) < 6:
                continue
            cc = list(conds)
            rng.shuffle(cc)
            h1, h2 = cc[: len(cc) // 2], cc[len(cc) // 2:]
            inc = float(np.mean([np.std([md[m][k] for k in h1]) for m in models]))
            w = kendalls_w(np.array([[md[m][k] for m in models] for k in h2]))
            if not np.isnan(w):
                inc_h.append(inc)
                W_h.append(w)
        split_rs.append(spearman(np.array(inc_h), np.array(W_h)))
    return {"n_models": len(models), "n_items": int(len(incons)), "rho": r, "perm_p": p,
            "W_mean": float(W.mean()), "inconsistency_mean": float(incons.mean()),
            "split_half_rho_mean": float(np.mean(split_rs)), "split_half_rho_sd": float(np.std(split_rs))}


def gating_null(rows, draws=20, seed=0, split_half=False):
    """No-mechanism null: per proposition and model, keep the mean and SD of the stance across the non-negation
    conditions, redraw each condition's value independently from N(mean, SD), and recompute rho. What survives is
    the coupling between spread and ordering that any data with these spreads would show."""
    models = sorted({c["model"] for c in rows})
    table = _gating_table(rows)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(draws):
        null_rows = []
        for it in sorted(table):
            md = table[it]
            conds = sorted(set.intersection(*[set(md[m]) for m in models]))
            for m in models:
                x = np.array([md[m][k] for k in conds])
                y = rng.normal(x.mean(), x.std(), len(conds))
                null_rows += [{"item_id": it, "model": m, "condition_key": k, "condition_factor": "x", "stance": float(v)}
                              for k, v in zip(conds, y)]
        g = gating(null_rows, perm_B=0, n_splits=20 if split_half else 1, seed=int(rng.integers(1 << 31)))
        out.append(g["split_half_rho_mean"] if split_half else g["rho"])
    return {"mean": float(np.mean(out)), "sd": float(np.std(out)), "draws": draws}


# --------------------------------------------------------------------------- condition effects
def condition_effects(rows):
    """Mean |stance - default stance| per condition family, and the signed mean shift under each pressure."""
    default = {}
    for c in rows:
        if c.get("condition_factor") == "default":
            default[(c["model"], c["item_id"])] = c["stance"]
    fac = defaultdict(list)
    by_key = defaultdict(list)
    for c in rows:
        f = c.get("condition_factor", "?")
        if f in ("default", "?"):
            continue
        d = default.get((c["model"], c["item_id"]))
        if d is not None:
            fac[f].append(abs(c["stance"] - d))
            by_key[c["condition_key"]].append(c["stance"] - d)
    by_factor = sorted(([f, float(np.mean(v)), len(v)] for f, v in fac.items()), key=lambda r: -r[1])
    pressure = {k.split("=", 1)[1]: float(np.mean(v)) for k, v in by_key.items() if k.startswith("pressure=")}
    return {"effect_by_factor": by_factor, "pressure_signed_delta": pressure}
