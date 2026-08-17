# Same-writer semantic replay

After the final consolidated correction and successful complete build, the
single controlling Hindi writer replayed the corpus at whole-reader level.

The replay checked the 722/722 source-to-target path census, stable IDs, language
markers, environment order, labels, references, citations, imports, token
resolution, and reader-facing English leakage. Diagnostic mismatches in exact
whole-file formula occurrence multisets were treated as advisory rather than
silently forced: Hindi legitimately reorders clauses, translates prose inside
math text nodes, and can avoid repeating an inline formula already displayed.
The mismatching categories were triaged against command deltas and the final
render; no unledgered formal defect was confirmed.

All proper names, bibliography entries, work titles, URLs, acronyms, code
identifiers, and mathematical symbols retained in Latin script were classified
as source-facing identifiers or documentary titles rather than untranslated
reader prose. The only three deliberate source/formal deviations are enumerated
in \`SOURCE_DIFF_LEDGER.jsonl\`.

This is an honest same-writer replay. It is not independent AI review, human
review, native-speaker certification, peer review, or a critical-edition claim.
