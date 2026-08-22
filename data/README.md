# `data/` — the corpus

**76,048 elicited stances = 4 models × 388 propositions × 49 phrasing conditions.**

Every combination was asked exactly once, so the design is balanced: each of the 49 conditions has
exactly **1,552 rows** (4 × 388), and each model contributes exactly **19,012**.

```
data/
  battery.jsonl        the 388 propositions that were asked
  responses.jsonl.gz   the 76,048 answers          <- the raw log
  atlas/               pos_reflection.bin, the one layout that cannot be recomputed
                       (see atlas/README.md; everything else rebuilds from the log)
```

See the [top-level README](../README.md) for what the numbers mean and for the limits you should
know about before using any of this.

---

## `battery.jsonl` — the propositions

One JSON object per line, 388 lines.

```json
{
  "id": "eth.welfare",
  "domain": "ethics",
  "proposition": "The moral worth of an action is determined mainly by its consequences.",
  "facets": ["Intentions matter less than outcomes.",
             "Maximizing overall welfare is the right goal."],
  "subtopic": "",
  "contested": null,
  "polarity": 1,
  "negation": "",
  "split": "train",
  "source": {"type": "curated", "generator_model": "", "human_approved": true,
             "dataset": "", "dataset_license": "", "original_id": "", "url": "",
             "ref_dist": "", "reviewed_by": "", "review_date": ""}
}
```

| field | meaning |
|---|---|
| `id` | stable key, `<prefix>.<slug>`. Joins to `item_id` in the answer log. |
| `domain` | one of the ten topics below. |
| `proposition` | the statement the model was asked to agree or disagree with. |
| `facets` | one or two sub-claims the proposition bundles together. 305 items have 2, 83 have 1. |
| `subtopic` | free-text grouping. Present on the 356 machine-written items, empty on the 32 curated ones. |
| `contested` | whether the statement is genuinely disputed. `true` 293, `false` 63, `null` 32 (never set on the curated items). |
| `polarity` | `1` if agreeing means endorsing the claim, `-1` if the wording is reversed. 368 are `1`, 20 are `-1`. |
| `negation` | a negated restatement, used by the `polarity` conditions. Present on 356 items, empty on the 32 curated ones. |
| `split` | `train` (350) or `held_out` (38). **Nothing in this release uses the split** — it was reserved for work that has not run. |
| `source` | provenance. See the warning below. |

### Topics

| domain | items | | domain | items |
|---|---:|---|---|---:|
| ethics | 47 | | technology | 42 |
| politics | 47 | | social | 45 |
| economics | 40 | | aesthetics | 26 |
| science | 40 | | values | 30 |
| metaphysics | 35 | | **factual-control** | 36 |

`factual-control` is not an opinion topic. It holds statements with actual right answers, and exists
as a sanity check: a measurement instrument that makes these look as contested as ethics is
mismeasuring something.

### Most of these propositions were written by a model

**32 of 388** were curated by hand (`source.type: "curated"`, `human_approved: true`). The other
**356** were drafted by a language model (`source.type: "llm-authored"`,
`generator_model: "workflow:claude-opus"`, `human_approved: false`), then deduplicated and linted
programmatically — but **not reviewed by a person**. If you build on this battery, that is the first
thing to check for yourself.

---

## `responses.jsonl.gz` — the answers

Gzipped JSON Lines, 76,048 lines. Each line wraps a cache key around the record you want:

```json
{"key": "ba6cc4a5...", "value": { ... }}
```

```python
import gzip, json

with gzip.open("data/responses.jsonl.gz", "rt") as f:
    for line in f:
        v = json.loads(line)["value"]
        ...
```

All 76,048 rows store `value` as a JSON object; we checked every one. Nothing else is needed.

| field | type | meaning |
|---|---|---|
| `model` | str | one of the four provider IDs below |
| `item_id` | str | joins to `id` in `battery.jsonl` |
| `domain` | str | copied from the battery, for convenience |
| `condition_key` | str | the exact phrasing condition, e.g. `option_order=reversed` |
| `condition_factor` | str | which family that condition belongs to |
| `stance` | float | **−1 disagrees … +1 agrees.** The expected value over the five option probabilities. |
| `likert` | int | 0–4. A deterministic rounding of `stance`, **not a separately given answer.** |
| `entropy` | float | how spread the five option probabilities were. 0 = certain, ~1 = flat. |
| `option_logprobs` | list[5] | log-probability of each answer option |
| `justification` | str | the model's own written reasoning |
| `logprob_source` | str | `native` or `sampling` — **see the warning below** |
| `refused` | bool | **does not mark refusals.** See below. |
| `in_tokens`, `out_tokens` | int | token counts for that call |

### `likert` is a rounding of `stance`, not a second opinion

`likert == round((stance + 1) / 2 * 4)` for **all 76,048 rows, with zero exceptions.** It is not a
separately elicited rating. Treating the two as independent readouts of the same answer will
manufacture agreement that is not there — a correlation between them measures rounding, nothing
more. A genuinely independent agreement rating exists only in a separate 1,552-row sub-collection
that is **not** part of this release.

### Half the probabilities are estimates

| `logprob_source` | rows | share | what it means |
|---|---:|---:|---|
| `native` | 37,154 | 48.9% | true log-probabilities: all 19,012 `gpt-4o-mini` rows, and 18,142 of 19,012 `llama-3.3-70b` |
| `sampling` | 38,894 | 51.1% | no logprobs returned, so **estimated from up to three draws**: all of `qwen-2.5-72b` and `deepseek-chat`, plus the 870 `llama-3.3-70b` rows the API did not serve |

The sampled estimator can never place more than `3.5/5.5 = 0.636` on any option (verified: the
maximum over the 38,713 genuinely sampled rows is 0.636364; the 181 parse-failure rows described
below carry a synthetic distribution instead), so it has a hard entropy floor the native rows do not
have. **The two halves are not comparable as uncertainty measures**, and the split is almost
entirely determined by model identity — three of the four models are 100% one route, and only
`llama-3.3-70b` is mixed — so any comparison of "uncertainty" across models is largely a comparison
of how the probabilities were obtained.

### `refused` does not mark refusals

All **181** rows flagged `refused: true` carry substantive answers; they are parse failures. Rows
that do contain genuine refusal language are not flagged at all. How many depends entirely on the
matching rule you choose, so we give no count rather than one you cannot reproduce from these files.

### The four models

`meta-llama/llama-3.3-70b-instruct` · `qwen/qwen-2.5-72b-instruct` · `deepseek/deepseek-chat` ·
`gpt-4o-mini`

Obtained through the OpenAI and OpenRouter APIs. `manifest.json` lists them in this order, and any
model index you rebuild follows it.

---

## The 49 phrasing conditions

The whole point of the corpus: the same proposition asked 49 different ways.

| family | conditions | rows | what varies |
|---|---:|---:|---|
| `persona` | 30 | 46,560 | the model is told to answer *as someone* |
| `system_prompt` | 4 | 6,208 | `blank`, `neutral_assistant`, `expert_panel`, `devils_advocate` |
| `pressure` | 4 | 6,208 | the user pushes back: `agree_push`, `disagree_push`, `authority`, `repeat_challenge` |
| `framing` | 3 | 4,656 | three paraphrases of the same question |
| `option_labels` | 3 | 4,656 | the answer options are relabelled: `numeric`, `flipped_numeric`, `letters` |
| `polarity` | 2 | 3,104 | the proposition is `negated` or `double_negated` |
| `option_order` | 2 | 3,104 | the options are `reversed` or `shuffled` |
| `default` | 1 | 1,552 | the unperturbed baseline prompt |

**Row share is a roster artifact, not a measure of importance.** Persona dominates the corpus because
30 personas were tried, not because persona matters 30 times more than option order. The design is
balanced per condition, not per family.

### The 30 personas

- **16 countries** — Brazil, China, Egypt, France, Germany, India, Indonesia, Japan, Mexico, Nigeria,
  Russia, Saudi Arabia, South Africa, Sweden, the United Kingdom, the United States
- **8 occupational roles** — a civil-liberties advocate, a climate scientist, a moral philosopher, a
  political scientist, a public-health official, a religious scholar, an economist, an entrepreneur
- **6 political leanings** — a centrist, a libertarian, a nationalist, a political conservative, a
  political progressive, a socialist

> **These are model artifacts produced under instructed roleplay.** They are evidence about how a
> model's expressed stance shifts when you tell it who to be. They are **not** evidence about any
> real population, and must not be cited as opinion data about a country, profession or political
> group. Many of the 24,832 country-persona answers slip into a first-person national voice and
> generalize about a named country's people; how many depends entirely on the phrase pattern you
> match, so look rather than take a count from us.

---

## Joining the three files

`item_id` joins the answer log to the battery. **Row order joins the log to the layout**: line *i* of
`responses.jsonl.gz` is row *i* of `atlas/pos_reflection.bin`, and of any array you rebuild from the
recipe in [`atlas/README.md`](atlas/README.md#the-rebuild-recipe). Verified over the whole corpus.

```python
import gzip, json, numpy as np

battery = {json.loads(l)["id"]: json.loads(l) for l in open("data/battery.jsonl")}
xy      = np.fromfile("data/atlas/pos_reflection.bin", "<f4").reshape(-1, 2)   # (76048, 2)

with gzip.open("data/responses.jsonl.gz", "rt") as f:
    for i, line in enumerate(f):
        v = json.loads(line)["value"]
        prop = battery[v["item_id"]]["proposition"]     # the statement that was asked
        x, y = xy[i]                                    # where it sits in panel 1
```

---

## Before you use `stance`

`stance` carries a known defect: a matcher that collides on shared words records answers as neutral
even where the model's own `justification` is decisive. The signature is
`option_logprobs[0] == option_logprobs[4] == max(option_logprobs)`, and it marks **18,420 of the
75,867 non-refused rows (24.3%)**; 77.8% of those open with an explicit "agree" or "disagree", and
6,141 (8.1%) land at a stance of essentially zero.

**Only `justification` escaped it.** `option_logprobs` is the matcher's own output, not a raw
reading: in 69,129 rows (90.9%) it holds the identical log-probability for the two opposite extremes,
and recomputing a stance from it reproduces the shipped value to within 3 × 10⁻⁸ — the same wrong
number. Recompute from the free text. Details and a worked example are in the
[top-level README](../README.md#two-bugs-we-found-in-our-own-code).

Licensed CC BY 4.0 — see [LICENSE](../LICENSE).
