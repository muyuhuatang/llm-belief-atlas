# LLM Belief Atlas

**What a language model appears to believe depends on how you ask it — and on how you read the answer.**

IEEE VIS 2026 Posters · Fan Huang, Indiana University Bloomington · `huangfan@acm.org`

This repository holds the data behind the poster: **76,048 elicited stances** from four language
models, and the coordinates that draw the poster's figures.

---

## The idea, in one minute

Ask a model *"Is the moral worth of an action determined mainly by its consequences?"* and you can
read its answer three different ways:

1. **Read what it wrote.** It gives you a paragraph of reasoning.
2. **Read the probabilities.** Behind the scenes it assigned a probability to each answer option.
3. **Read the rating.** You can turn that into a 5-level agree/disagree score.

These are three *readouts of the same answer*. They should agree. **They don't.** And the way you
phrased the question — the persona you gave it, whether you reversed the option order, whether you
pushed back — moves the answer about as much as the topic does.

So "what does this model believe?" is not a question with one number for an answer. It is a
**measurement problem**. This project treats it as one.

---

## What the poster shows

![Three readouts of the same 76,048 answers](images/three-channels.png)

**One dot is one answer** — one model, on one proposition, under one phrasing. All 76,048 dots go
into every panel; only the *layout* changes, because each panel arranges them by a different readout.
(Each panel is cropped to its central 98.8%, so a couple of thousand outliers fall outside the frame
rather than squashing everything else into the middle.)

- **Panel 1 — Reflection.** The model's own words, turned into coordinates. Dots that sit near each
  other used similar language. Color is the **topic**.
- **Panel 2 — Logprob.** The probabilities it put on each answer option. Color is the **stance**:
  blue disagrees, red agrees, pale grey is neutral.
- **Panel 3 — Agreement.** The agreement readout as a stance value, spread out with one row per topic
  so you can see how each topic leans. The black tick on each row is that topic's average.

**The nine numbered rings are the same nine beliefs in every panel.** That is the whole point of the
picture. Find the ringed anchor 3 — a politics belief — in each one. It is one dot, so its *stance* is
the same number in all three, and yet it lands in a completely different neighbourhood each time. **Where the three panels disagree about a dot, that
disagreement is the measurement.**

### Why the map can fool you

![Density over the reflection layout](images/density.png)

Past roughly one dot per pixel, a scatterplot stops showing you how many points are somewhere and
starts showing you *which point was drawn last*. This counts instead: every one of the 76,048 answers
falls in a bin, pale yellow means a bin holds one, dark purple means it holds up to 35, and the scale
is logarithmic because the range is wide. Any claim about where the cloud is dense should be read off
a picture like this one, not off the scatterplots above.

---

## What we found

**How you ask matters about as much as what you ask about.** Splitting the variation in stance:
the **phrasing condition explains 27.05%**, and **belief structure explains 35.90%** (the remaining
37.05% is residual). Those are the same order of magnitude, which is the finding. Note what the
second figure is made of: the proposition alone accounts for 16.13%, the proposition-and-model
interaction for 15.52%, and the model alone for 4.25%. So less than half of "belief" is a property
of the proposition by itself; most of it depends on which model you asked.

> **Read that partition carefully.** It is not one number the analysis hands you — it is a *collapse*
> of seven variance components into three groups, under a grouping rule we chose, and the rule is
> load-bearing. All three figures reproduce exactly from this corpus under that rule. Under other
> defensible groupings the headline moves, and under some of them belief dominates condition
> outright. The claim that survived the groupings we tried is the weaker, more useful one: **how you
> ask is not a rounding error next to what you ask about.**

**Relabelling or reordering the answer options moves a stance at least as much as rewording the
question does.** We are not giving an effect size for this, because two bugs in our own code inflate
exactly this comparison — see below. The direction holds; the magnitude is being re-derived.

**The 49 phrasings are not equally represented**, and the roster is a design choice, not a measure of
importance:

| phrasing family | rows | share |
|---|---:|---:|
| persona (told to be someone) | 46,560 | 61.2% |
| system-prompt framing | 6,208 | 8.2% |
| user pressure (pushing back) | 6,208 | 8.2% |
| question paraphrase | 4,656 | 6.1% |
| option relabelling | 4,656 | 6.1% |
| negation | 3,104 | 4.1% |
| option reordering | 3,104 | 4.1% |
| plain default (the unperturbed baseline prompt) | 1,552 | 2.0% |

---

## What is in `data/`

```
README.md              this file
LICENSE
data/
  battery.jsonl        the 388 propositions that were asked
  responses.jsonl.gz   the raw log: all 76,048 answers
  atlas/
    pos_reflection.bin the one layout that cannot be recomputed
    manifest.json      labels, counts, format
images/                the two figures used above
```

Twelve files. Everything the poster draws is either in that list or rebuilds from it — see
[`data/atlas/README.md`](data/atlas/README.md#the-rebuild-recipe).

Each folder has its own README with the full field-by-field reference:
[`data/`](data/README.md) · [`data/atlas/`](data/atlas/README.md) · [`images/`](images/README.md).

`76,048 = 4 models × 388 propositions × 49 phrasing conditions.` Every combination appears exactly
once, so the design is balanced. That is a count of *combinations*, not of API calls — each cell took
more than one call, so the collection issued several times that many.

**The four models:** `llama-3.3-70b-instruct`, `qwen-2.5-72b-instruct`, `deepseek-chat`, `gpt-4o-mini`.

**The ten topics:** ethics, politics, economics, science, metaphysics, technology, social,
aesthetics, values, and a **factual-control** group of propositions with actual right answers, used
as a sanity check.

### One row of `responses.jsonl.gz`

Each line is `{"key": ..., "value": {...}}`. The `value` holds fourteen fields; here are twelve of
them (`in_tokens` and `out_tokens` complete the set):

```python
{'model': 'qwen/qwen-2.5-72b-instruct',
 'item_id': 'sci.method',
 'domain': 'science',
 'condition_key': 'option_order=reversed',   # how the question was phrased
 'condition_factor': 'option_order',
 'stance': 0.545,                            # -1 disagrees ... +1 agrees
 'likert': 3,                                # 0..4, a rounding of `stance`
 'entropy': 0.720,                           # how spread its probabilities were
 'option_logprobs': [...],                   # 5 numbers, one per answer option
 'justification': 'strongly agree; The scientific method systematically tests ...',
 'logprob_source': 'sampling',               # 'native' or 'sampling' — see below
 'refused': False}
```

### Reading `atlas/`

`atlas/` ships **one** array — `pos_reflection.bin`, the layout panel 1 is drawn from. It is the only
one that cannot be recomputed, because it comes from a sentence embedding that is not in this
release. Everything else the poster uses (the stance, entropy and topic values, and the other two
layouts) was a cache and rebuilds exactly from `responses.jsonl.gz`; the tested recipe is in
[`data/atlas/README.md`](data/atlas/README.md#the-rebuild-recipe).

`float32`, little-endian, no header: 76,048 records of `(x, y)`. **Row *i* is line *i* of
`responses.jsonl.gz`.**

```python
import gzip, json, numpy as np

m  = json.load(open("data/atlas/manifest.json"))
xy = np.fromfile("data/atlas/pos_reflection.bin", "<f4").reshape(-1, 2)   # (76048, 2)

names = m["attributes"]["domain"]["labels"]        # ['ethics', 'politics', ...]
with gzip.open("data/responses.jsonl.gz", "rt") as f:
    dom = np.array([names.index(json.loads(l)["value"]["domain"]) for l in f], np.uint8)

# every dot in panel 1, coloured by topic — this is the left panel above
import matplotlib.pyplot as plt
plt.scatter(xy[:, 0], xy[:, 1], c=dom, s=1, alpha=0.4, cmap="tab10")
```

---

## Honest limits

The contribution here is an argument about *measurement*, so overselling it would defeat the point.

### Two bugs we found in our own code

While tracing every number back to its source we found two defects in the code that turns a model's
answer into a stance score:

1. A matcher that collides on shared words, recording answers as neutral even when the model's own
   text is decisive.
2. A parser that scores the letter option "A" for any answer containing the word "agree".

How big is the first one? The collision leaves a signature you can grep for: the same
log-probability on both extreme options, and that value is the maximum of the five. Counting it:

```python
lp = v["option_logprobs"]
collided = (lp[0] == lp[4] == max(lp))     # 18,420 of the 75,867 non-refused rows = 24.3%
```

**24.3% of the corpus carries that signature**, and **77.8% of those rows open with an explicit
"agree" or "disagree"** in the free text. 6,141 rows (8.1%) end up at a stance of essentially zero
as a result.

Here is a real row that shows the first one. The model plainly agrees, and the stance says neutral:

```python
{'item_id': 'eth.welfare', 'domain': 'ethics',
 'condition_key': 'persona=a climate scientist.persona_kind=role',
 'justification': 'strongly agree. As a climate scientist, I believe that the moral worth ...',
 'stance': 0.0007}          # <- should be near +1
```

Because stance is computed from the stored probabilities, it reaches the stance array and therefore
the colours in panels 2 and 3. **Two findings were withdrawn** as a result: the
option-relabelling effect size, and the per-model correlations between readouts.

**Recompute from `justification`, not from `option_logprobs`.** This is the trap. The stored
`option_logprobs` vector is the matcher's *own output*, not a raw model reading — in **69,129 of the
76,048 rows (90.9%)** it assigns the identical log-probability to the two opposite extremes, which is
the collision itself. Recomputing a stance from it reproduces the wrong value exactly (we checked:
maximum difference from the shipped `stance` is 3 × 10⁻⁸). The free text is the only field the
defect never touched.

### Half the probabilities are estimates, not true logprobs

**37,154 rows (48.9%)** carry natively-read option probabilities: all of `gpt-4o-mini`, and 18,142 of
the 19,012 `llama-3.3-70b` rows. The other **38,894 rows (51.1%)** were estimated by sampling: all of
`qwen-2.5-72b` and `deepseek-chat`, plus the 870 `llama-3.3-70b` rows where the API returned no
logprobs. The estimate uses up to three draws, not always three. The `logprob_source` field tells you
which route any given row took.
These two halves are **not comparable** as uncertainty measures, and any result that leans on
`entropy` across all four models inherits that.

### The `refused` flag does not mark refusals

All **181** rows flagged `refused` carry substantive answers — they are parse failures. Rows that do
contain actual refusal language are not flagged at all; how many depends on the matching rule, so we
give no count rather than one you cannot reproduce from these files.

### Most propositions are machine-written

**32 of 388** were written by hand. The other **356** were drafted by a language model
(`generator_model: workflow:claude-opus`, `human_approved: false`), then deduplicated and checked
programmatically — but not reviewed by a person.

### No human validation

The perception study was designed but never run; the only data is one annotator over ten trials.
There is no comparison against a simpler visualization, so whether this technique's complexity earns
its keep is **an open question, not a settled one**. The framework names a human-calibration
subspace; it is empty, because no human opinion data was collected.

### Where the numbers came from is not fully logged

The collection code that produced `data/` is not published, and the exact prompts are not recoverable
from these files. The counts above are reconstructed from the data itself. That is strong evidence,
but it is not a logged record, and we say so rather than implying otherwise.

---

## Please do not use the persona rows as opinion data

**46,560 of the 76,048 rows (61.2%) are persona conditions** — the model was told to answer as
someone: 16 named countries, 8 occupational roles, and 6 political leanings.

These are **model artifacts produced under instructed roleplay**. They are evidence about how a
model's expressed stance shifts when you tell it who to be. They are **not** evidence about any real
population, and must not be cited as opinion data about a country, profession or political group.

Many of the 24,832 country-persona answers slip into a first-person national voice and generalize
about a named country's people. We give no count: it depends entirely on the phrase pattern you
match, and we would rather you look than take a number from us.

---

## Citation

```bibtex
@inproceedings{huang2026beliefatlas,
  title     = {The {LLM} Belief Atlas: Visualizing How Language-Model Stances Depend on Elicitation},
  author    = {Huang, Fan},
  booktitle = {IEEE VIS 2026 Posters},
  year      = {2026}
}
```

## License

Data and documentation are CC BY 4.0 — see [LICENSE](LICENSE). The corpus contains outputs from
Llama-3.3-70B, Qwen-2.5-72B, DeepSeek-V3 and GPT-4o-mini; anyone redistributing the raw generations
should check the relevant providers' terms.
