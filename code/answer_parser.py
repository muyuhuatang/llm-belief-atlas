"""How a written answer is mapped to one of the five options: the corrected parser, and the original one for reference.

The original parser walked the presented labels in presentation order and returned the first label that began the
answer or appeared after a space. Three errors followed:
  * a shorter label inside a longer answer won: "strongly agree" was read as "agree", and "neither agree nor
    disagree" as "disagree" (or as "agree" when the options were presented in reversed order);
  * a one-character label matched the first letter of any word: under letters A-E, an answer beginning "agree"
    was read as option A.
The corrected parser:
  1. normalizes the answer (strip, lowercase, drop leading markdown, quotes and brackets);
  2. reads a one-character label (A-E, 1-5) only when it stands alone at the start;
  3. otherwise takes the LONGEST presented label or option text that begins the answer;
  4. otherwise takes the longest option text appearing anywhere as a whole phrase, masking each match; answers
     naming two different options are left unread (None).
It adds no synonyms: "neutral", for instance, stays unread, as it was.

`label_to_canonical` maps each presented label, in presentation order, to its option index: 0 = strongly disagree
... 4 = strongly agree.
"""
from __future__ import annotations

import re

LIKERT_OPTIONS = ("strongly disagree", "disagree", "neither agree nor disagree", "agree", "strongly agree")
_LEAD = re.compile(r"^[\s\*\"'`_#>\-\(\[\{]+")


def parse(text: str, label_to_canonical: dict) -> int | None:
    t = _LEAD.sub("", (text or "").strip().lower())
    if not t:
        return None
    labels = {str(lab).lower(): int(c) for lab, c in label_to_canonical.items()}
    short = {lab: c for lab, c in labels.items() if len(lab) == 1}
    if short:
        m = re.match(r"^([a-z0-9])(?=$|[^a-z0-9])", t)
        if m and m.group(1) in short:
            return short[m.group(1)]
    phrases = {lab: c for lab, c in labels.items() if len(lab) > 1}
    for c, opt in enumerate(LIKERT_OPTIONS):
        phrases.setdefault(opt, c)
    for ph in sorted(phrases, key=len, reverse=True):
        if re.match(re.escape(ph) + r"(?=$|[^a-z])", t):
            return phrases[ph]
    found, masked = set(), t
    for ph in sorted(phrases, key=len, reverse=True):
        pat = re.compile(r"(?<![a-z])" + re.escape(ph) + r"(?![a-z])")
        if pat.search(masked):
            found.add(phrases[ph])
            masked = pat.sub(lambda m: "#" * len(m.group(0)), masked)
    return found.pop() if len(found) == 1 else None


def original_parse(text: str, label_to_canonical: dict) -> int | None:
    """The parser the first collection used, kept to show the errors above."""
    t = text.strip().lower()
    for lab, canon in label_to_canonical.items():
        if t.startswith(lab.lower()) or f" {lab.lower()}" in f" {t}":
            return canon
    for canon, opt in enumerate(LIKERT_OPTIONS):
        if opt.lower() in t:
            return canon
    return None
