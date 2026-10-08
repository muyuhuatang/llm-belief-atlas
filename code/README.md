# `code/`: checking the correction and reproducing the numbers

Six plain Python files. They need Python 3.9 or later and numpy (`pip install -r requirements.txt`), and nothing
else. Every script reads only files in [`../data/`](../data/), so a fresh clone can run all of them. Run them from
the repository root:

```bash
python code/test_answer_parser.py        # the corrected answer parser, on every label scheme (seconds)
python code/verify_correction.py         # every corrected row follows from the original row + its record (20 s)
python code/reproduce_statistics.py      # the summary's statistics from the corrected corpus (about 5 min)
python code/three_channel_subset.py      # the three-readout convergence and method variance (seconds)
```

| File | What it does |
|---|---|
| `belief_stats.py` | The statistics as functions. The variance decomposition, the proposition bootstrap and the reliability-gating test are copied without change from the scripts that produced the poster's numbers. The no-mechanism null and the condition-effect summary are written out here. |
| `reproduce_statistics.py` | Prints the variance split (four models, and the two natively-read ones), its 95% bootstrap intervals and seven components; the gating correlation with its null; the shifts under user pressure and per condition family; and Table 1. `--corpus data/responses.jsonl.gz` reproduces the numbers originally published with the poster. `--sign-rule` is the sensitivity analysis described in the top-level README. `--out FILE` writes every value as JSON. |
| `three_channel_subset.py` | Correlations between the three readouts on the 1,552-cell subset, overall and per model, and each readout's method-specific variance. `--original` uses the readouts as first collected. `--sign-rule` is the sensitivity analysis. |
| `verify_correction.py` | Rebuilds all 76,048 corrected rows from `responses.jsonl.gz` and each row's `correction` record, and requires exact equality with `responses_corrected.jsonl.gz`. It also checks that each record's flags match the original row. |
| `answer_parser.py` | The corrected parser that read the October answers, and the original parser, kept to show its errors. |
| `test_answer_parser.py` | 180 cases: six label schemes × five answers × six answer forms. The corrected parser must read all of them. The original must fail the known ones, or the test could not tell the two apart. |

**What the scripts reproduce:**
- **Corrected corpus:** every statistic in the corrected two-page summary.
- **Original log** (`--corpus data/responses.jsonl.gz`, `--original`): the values published with the poster, with
  one exception. The three readouts' sign agreement comes out at 80.2% instead of 80.1%, because the subset's
  reflection scores were recomputed from a new embedding call. They match the original scores to three decimals.
- **Determinism:** seeds are fixed, so repeated runs print the same numbers.

**License:** MIT, as the CODE section of [`../LICENSE`](../LICENSE) states. The data the scripts read
is CC BY 4.0.

## What is not here, and why

- **The collection code** (prompt templates for the 49 conditions, and the API calls), including the October
  re-elicitation. It needs API keys and calls paid services, and it was not part of the original release. The
  re-elicitation's settings are in the [top-level README](../README.md#five-bugs-we-found-in-our-own-code), and its
  results are in `../data/`.
- **Everything the API calls returned beyond the values in `../data/`:** the raw responses, the October answer texts,
  serving providers, token counts, costs, and embedding vectors. These are provider outputs and usage records. The
  data keeps only the values derived from them: option probabilities, categories counted, projections.
- **Figure scripts.** The figures are in [`../images/`](../images/). The arrays behind them rebuild from the corpus
  with the recipe in [`../data/atlas/README.md`](../data/atlas/README.md#the-rebuild-recipe).
