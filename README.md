# LLM Belief Atlas

**What a language model appears to believe depends on how you ask it — and on how you read the answer.**

IEEE VIS 2026 Posters · Fan Huang, Indiana University Bloomington · `huangfan@acm.org`

This repository holds the data behind the poster: **76,048 elicited stances** from four language
models, and the coordinates that draw the poster's figures.

**Since October 2026 it also holds a corrected corpus.** We found five bugs in how the original answers were scored.
We repaired what the stored data allowed and re-elicited the rest ([details](#five-bugs-we-found-in-our-own-code)).
- The **corrected two-page summary (arXiv version)** is computed from the corrected corpus.
- The **numbers published with the VIS poster** (on the poster and in its two-page summary) come from the original
  log.

Both are here, and [`code/`](code/) reproduces either set of numbers.

---

## The idea, in one minute

Ask a model *"Is the moral worth of an action determined mainly by its consequences?"* and you can
read its answer three different ways:

1. **Read what it wrote.** It gives you a paragraph of reasoning.
2. **Read the probabilities.** Behind the scenes it assigned a probability to each answer option.
3. **Read the rating.** You can turn that into a 5-level agree/disagree score.

These are three *readouts of the same answer*. They should agree. **They only partly do:** the rating and the
probabilities track each other closely, but what the model writes often points elsewhere. And the way you phrased the
question moves the answer a lot: the persona you gave it, whether you reversed the option order, whether you pushed
back. Together, those choices account for a third of all the variation in stance.

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

Panels 2 and 3 are drawn from the original scoring, which the bugs [below](#five-bugs-we-found-in-our-own-code)
distort; panel 1 is not affected. [The corrected picture](#the-corrected-picture) follows.

**The nine numbered rings are the same nine beliefs in every panel.** That is the whole point of the
picture. Find the ringed anchor 3 — a politics belief — in each one. It is one dot, so its *stance* is
the same number in all three, and yet it lands in a completely different neighbourhood each time. **Where the three panels disagree about a dot, that
disagreement is the measurement.**

### The corrected picture

![The corrected three readouts](images/three-channels-corrected.png)

The same idea, drawn from the corrected corpus. This is the corrected two-page summary's Figure 1, so it uses the
summary's layout: (a) agreement, (b) reflection, (c) logprob.
- In panel (a), decisive answers that the original scoring had flattened toward neutral now sit at both ends of each
  topic's row.
- Panel (b) is unchanged.
- The nine anchors were re-chosen on the corrected values by the same rule
  ([details](images/README.md#three-channels-correctedpng)).

### Why the map can fool you

![Density over the reflection layout](images/density.png)

Past roughly one dot per pixel, a scatterplot stops showing you how many points are somewhere and
starts showing you *which point was drawn last*. This counts instead: every one of the 76,048 answers
falls in a bin, pale yellow means a bin holds one, dark purple means it holds up to 35, and the scale
is logarithmic because the range is wide. Any claim about where the cloud is dense should be read off
a picture like this one, not off the scatterplots above.

---

## What we found

All numbers below come from the corrected corpus; `python code/reproduce_statistics.py` prints them. The values the
original scoring gave, as published with the poster, are in brackets for the record.

**How you ask matters, though less than what you ask about.** Splitting the variation in stance:
- **belief structure explains 46.78%** (95% interval 42.83–50.42) [originally 35.90%];
- the **phrasing condition explains 34.18%** (31.51–37.17) [27.05%];
- the remaining 19.05% is residual [37.05%].

The original scoring had inflated the residual by flattening decisive answers toward neutral. Most of "belief" is
now the proposition by itself (31.27%, two-thirds of it). The proposition-and-model interaction is 8.22%, and the model
alone 7.29%.

> **Read that partition carefully.** It is not one number the analysis hands you — it is a *collapse*
> of seven variance components into three groups, under a grouping rule we chose, and the rule is
> load-bearing. All three figures reproduce exactly from the corrected corpus under that rule. Under other
> defensible groupings the headline moves. The claim that survived the groupings we tried is the
> weaker, more useful one: **how you ask is not a rounding error next to what you ask about.**

**On the two natively-read models** (GPT-4o-mini and Llama-3.3-70B, 38,024 cells), condition and belief are on par:
40.83% and 42.62%, with overlapping intervals [originally 37.60% and 22.00%, which the two-page summary called
condition *exceeding* belief; that claim is withdrawn].

**Within-model reliability does not predict cross-model agreement beyond chance.** More inconsistent propositions do
have less reproducible cross-model orderings (Spearman ρ = −0.75 over 388 propositions). But data with the same spread
and no mechanism at all gives ρ = −0.73 ± 0.02 [originally −0.55 against −0.229 ± 0.025].

**Pushback works mostly one way.** On the −1 … +1 scale, telling a model you disagree moves its stance by −0.95 on
average; telling it you agree moves it by +0.25 [originally −0.30 and +0.02].

**Relabelling the answer options moves a stance more than rewording the question, but neither is a big effect.**
Mean shift from the default stance, by condition family:

| negation | user pressure | system prompt | persona | option relabelling | option reordering | question paraphrase |
|---:|---:|---:|---:|---:|---:|---:|
| 0.604 | 0.356 | 0.236 | 0.218 | 0.129 | 0.114 | 0.094 |

The original relabelling effect, 0.398 and the largest, was inflated by two of the bugs.

**The three readouts converge unevenly.** On the 1,552-cell subset where all three were collected independently,
the rating and the probabilities correlate at 0.88. What the model writes correlates with each of them at 0.63–0.67. A
one-factor decomposition attributes to method 52% of the written readout's variance, 17% of the probabilities' and 7%
of the rating's [originally 41%, 49% and 11%].

**How robust are these numbers?** The repair has one free choice: how to split the tied "strongly" mass where it
could not be measured (see below). Every qualitative statement above holds with the alternative split, except the
native-model comparison. That one reverses (34.46% belief, 42.00% condition), which is why we call the two only on par.
`python code/reproduce_statistics.py --sign-rule` prints the alternative. The re-elicited half of the corpus is an
October 2026 measurement; see [Did the models change between June and
October?](#did-the-models-change-between-june-and-october)

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

## Five bugs we found in our own code

The 76,048 stances came by two routes:
- **Native, 37,154 rows** (all of GPT-4o-mini, most of Llama-3.3-70B): the API returned log-probabilities for the
  answer's first token, and a matcher assigned them to the five options.
- **Sampled, 38,894 rows** (all of Qwen-2.5-72B and DeepSeek-V3, and 870 Llama rows): the API returned none, so the
  model was asked three times and a text parser read each answer.

Both routes had bugs.

**In the log-probability matcher:**

1. **"Strongly" counted twice.** "Strongly disagree" and "strongly agree" share their first word, and the matcher gave
   the probability of "strong…" to both.
   - All 34,993 non-refused native rows with word labels have their two extremes tied. With numeric or letter labels,
     only 32 of 2,161 such rows do.
   - Wherever a model put weight on an extreme, its preference between the two extremes was lost and the stance was
     pulled toward zero.
   - In 18,420 of the 75,867 non-refused rows (24.3%), the tied extremes were also the top option, so a decisive answer
     was recorded as neutral. 14,327 of those (77.8%) open with an explicit "agree" or "disagree".
2. **An empty token matched every option.** When an empty or whitespace token was among the model's top candidates, it
   matched all five labels at once. This affected 512 native rows.

*Worked example* (the first line of `responses.jsonl.gz`): `llama-3.3-70b-instruct`, item `eth.welfare`, condition
`persona=a climate scientist.persona_kind=role`.
- The answer begins "strongly agree. As a climate scientist, I believe…".
- Its `option_logprobs` are `[-0.6946, -20.6916, -20.6916, -6.5696, -0.6946]`. "Strongly disagree" and "strongly
  agree" tie at the top, so `stance` is 0.0007 and `likert` is 2, the neutral midpoint.
- In `responses_corrected.jsonl.gz`, the same row has `stance` 0.9986 and `likert` 4.

**In the text parser**, which read every sampled answer and the separately asked rating of the three-readout subset.
It returned the first presented label it could find anywhere in the answer, which caused three errors:

3. **"Strongly agree" was read as "agree".** The shorter label inside the longer answer won.
4. **"Neither agree nor disagree" was read as "disagree"**, or as "agree" when the options were presented in reversed
   order. Under the usual option order, the 98,453 answers it read landed as follows: strongly disagree 7.0%, disagree
   32.6%, neither 0.0%, agree 60.5%, strongly agree 0.0%. Two of the five options were never recorded.
5. **A one-letter label matched any word starting with that letter.** Under letters A–E, an answer beginning "agree"
   was read as A, which was "strongly disagree". 82.4% of answers in that condition were recorded as strongly
   disagree.

**Why the bugs inflated the relabelling comparison.** Relabelled options (numbers, letters) share no words, so their
extremes almost never tie. Comparing them with word-label conditions therefore mixed a real elicitation effect with
bug 1, while bug 5 sent most letter-label answers to one extreme.

### What we did about them

- **The native rows were repaired from their own probabilities.**
  - The empty-token matches (bug 2) were removed.
  - In the tied rows, the "strong…" mass was split between the two extremes. For 17,564 of the 34,993 tied rows,
    carrying 87% of the tied probability, the split was measured. In October we asked the same prompt again and read
    the probabilities the model put on " agree" and " disagree" right after its own "strongly". These probes ran in
    October, on June's prompts, and were applied to June's probabilities. In October the API served GPT-4o-mini as the
    dated snapshot `gpt-4o-mini-2024-07-18`, and Llama's re-elicited answers did not drift (below).
  - In the other tied rows, the model's first answer never passed through "strongly", so the split follows the *sign
    rule*: all of the mass goes to the side the model favored between "agree" and "disagree". Where both exist and
    the tied share is above 5%, the sign rule picks the measured side on 97% of rows.
- **The sampled half could not be repaired**, because only the parser's counts had been kept, not the answers. So all
  38,894 sampled rows were re-elicited on 2026-10-06:
  - the same prompts, through the same API routes;
  - three answers each, at temperature 0.7 and at most 8 tokens;
  - each answer read by the corrected parser ([`code/answer_parser.py`](code/answer_parser.py)).
- **The three-readout subset** (1,552 cells):
  - the separately asked rating was re-asked the same day;
  - the probability readout was corrected as above;
  - the written justifications were re-embedded, which reproduced the original reflection scores to three decimals.
- **Not touched:** the written justifications in the main corpus, the reflection layout, and the design.

`python code/verify_correction.py` checks every corrected row against its original row and its `correction` record.

### Did the models change between June and October?

A re-elicitation only repairs the corpus if the model behind the API still answers the way it did. Before using the
October answers, we read them with the *original* parser and compared them with June's, under the usual option order.
The comparison uses the three categories that parser could produce, as shares of the answers it could read:

| model | June: SD / D+N / A+SA (unreadable) | October: SD / D+N / A+SA (unreadable) |
|---|---|---|
| DeepSeek-V3 | 6.7% / 33.7% / 59.6% (10.9%) | 6.5% / 38.1% / 55.4% (0.1%) |
| Qwen-2.5-72B | 7.0% / 32.4% / 60.7% (0.5%) | 7.0% / 32.0% / 61.0% (0.0%) |
| Llama-3.3-70B, 870 rows | 13.0% / 10.7% / 76.3% (5.3%) | 13.3% / 10.1% / 76.7% (3.6%) |

- **DeepSeek changed.** It now answers in the requested format almost every time. Its answers moved about four points
  from agreement toward disagreement or neutrality, including on prompts it had answered fully in June.
- **Qwen** moved by less than half a point, which is detectable only because there are 51,216 answers.
- **Llama** did not move.

So the corrected Qwen and DeepSeek readings are **an October 2026 measurement, not a reconstruction of June's**.

### What is safe to use

**Use `responses_corrected.jsonl.gz`.** In the original log, `stance`, `likert`, `entropy` and `option_logprobs` carry
the bugs above; only `justification` and the design fields escaped them.

---

## What is in this repository

```
README.md                        this file
LICENSE                          MIT for code/; CC BY 4.0 for data and documentation
requirements.txt                 numpy, for code/
InfoVis-poster.pdf               the display poster as presented at VIS
code/                            checks the correction and reproduces every number (see code/README.md)
data/
  battery.jsonl                  the 388 propositions that were asked
  responses_corrected.jsonl.gz   all 76,048 answers, corrected          <- use this one
  responses.jsonl.gz             all 76,048 answers as first scored     (the original numbers)
  three_channel_subset.jsonl     1,552 cells with three independent readouts, corrected
  atlas/
    pos_reflection.bin           the one layout that cannot be recomputed
    manifest.json                labels, counts, format
images/                          the poster's two figures, and the corrected figure
```

Twenty-three files, counting the folder READMEs. Everything the poster and the corrected summary draw is either in
that list or rebuilds from it; see [`data/atlas/README.md`](data/atlas/README.md#the-rebuild-recipe).

Each folder has its own README with the full field-by-field reference:
[`code/`](code/README.md) · [`data/`](data/README.md) · [`data/atlas/`](data/atlas/README.md) ·
[`images/`](images/README.md).

**What was left out, and why.**
- **Code:** only the code that checks the correction and computes the statistics is here. The collection code, which
  needs API keys and calls paid services, is not.
- **Data:** only values derived from the API calls are here. The raw API responses, the October answer texts, the
  serving providers, token counts and costs, and the embedding vectors are not.

`76,048 = 4 models × 388 propositions × 49 phrasing conditions.` Every combination appears exactly
once, so the design is balanced. That is a count of *combinations*, not of API calls — each cell took
more than one call, so the collection issued several times that many.

**The four models:** `llama-3.3-70b-instruct`, `qwen-2.5-72b-instruct`, `deepseek-chat`, `gpt-4o-mini`.

**The ten topics:** ethics, politics, economics, science, metaphysics, technology, social,
aesthetics, values, and a **factual-control** group of propositions with actual right answers, used
as a sanity check.

### One row of `responses_corrected.jsonl.gz`

Each line is `{"key": ..., "value": {...}}`. The `value` holds fifteen fields: the fourteen of the original log,
plus `correction`. Here are thirteen of them (`in_tokens` and `out_tokens` complete the set). This row reads the same
in both files: under the reversed option order, "strongly agree" was the first label, so the original parser read it
correctly.

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
 'logprob_source': 'sampling',               # 'native' or 'sampling' — see data/README.md
 'refused': False,
 'correction': {'kind': 'redrawn', 'redrawn_on': '2026-10-06', 'draws': 3,
                'parsed_counts': [0, 0, 0, 0, 3], 'unparsed': 0}}   # three "strongly agree" answers
```

### Reading `atlas/`

`atlas/` ships **one** array — `pos_reflection.bin`, the layout panel 1 is drawn from. It is the only
one that cannot be recomputed, because it comes from a sentence embedding that is not in this
release. Everything else the poster uses (the stance, entropy and topic values, and the other two
layouts) was a cache and rebuilds exactly from `responses.jsonl.gz`; the tested recipe is in
[`data/atlas/README.md`](data/atlas/README.md#the-rebuild-recipe). Run on `responses_corrected.jsonl.gz`, the same
recipe rebuilds the corrected arrays behind the corrected figure.

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

The code in [`code/`](code/) (with `requirements.txt`) is MIT-licensed; data and documentation are CC BY 4.0. Both
grants are in [LICENSE](LICENSE). The corpus contains outputs from
Llama-3.3-70B, Qwen-2.5-72B, DeepSeek-V3 and GPT-4o-mini; anyone redistributing the raw generations
should check the relevant providers' terms.
