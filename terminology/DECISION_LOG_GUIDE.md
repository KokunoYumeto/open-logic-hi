# Hindi Open Logic decision log

This public evidence shelf accompanies the complete Hindi reader. It is meant
for asynchronous expert correction, not as a review hold.

## Coverage

- 357 terminology decisions from `TERM_WEB.tsv`.
- 40 target correction events from `TARGET_CORRECTIONS.json`.
- 3 shared configuration decisions from `HELPER_CORRECTIONS.json`.
- Total: **400 traceable decision records** in `SUBSTANTIVE_DECISION_LOG.jsonl`.
- **20 explicitly provisional terms** are summarized in
  `PROVISIONAL_REVIEW_QUEUE.md`.

Every term record gives the English term, current Hindi wording, domain,
previously recorded authority, retrospective rationale, uncertainty, a precise
review question, and every exact literal occurrence found in the accepted 722
source/target file graph plus the Hindi locale configuration. The search is
literal and reproducible; a zero count does not prove conceptual absence and
does not catch inflection or macro indirection.

## Evidence honesty

The terminology backfill was generated on 2026-09-04 from earlier production
artifacts. Its rationales are explicitly labelled **retrospective** and are not
misrepresented as contemporaneous motives. `SOURCE_NOTES.md` records what
authorities were actually consulted, including failures and provisional
formations; this pass did not silently upgrade them to verified citations.
Correction-event motives are contemporaneous ledger text, while their expert
review questions are retrospective.

The rejected original correction bytes remain under
`qa/reconciliation/target-before-corrections/` in the public provenance ZIP.
This shelf never changes formal source authority or claims independent review.

## How to report a correction

Quote the `decision_id`, exact path/line, proposed Hindi replacement, intended
sense, and a stable native Hindi authority where available. A strong correction
should also state whether every listed occurrence changes or only a particular
context. Missing authority or unavailable experts never create a gap or hold;
the current choice remains a documented provisional resolution.
