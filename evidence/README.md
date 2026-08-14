# Evidence map

Start with these small files:

- `RELEASE_METADATA.json`: exact identity, DOI, scope, and reader hash
- `ACCEPTED_FILES.csv`: all 158 source/target pairs, sizes, and hashes
- `READER_COMPONENT_MANIFEST.json`: 18 components and physical page ranges
- `QA_STATE.json` and `QA_REPORT.md`: cumulative build/render QA summary
- `CUMULATIVE_READER_QA.json` and `MANUAL_VISUAL_REVIEW.md`: machine and direct
  visual-review receipts
- `COVERAGE_AND_CURSOR.md`: honest boundary and next chapter
- `SOURCE_AUTHORITY.json`: frozen source authority

The complete evidence payload is the numbered
`02_OpenLogic_hi-Deva-IN_PROVENANCE_AND_QA_158-of-722.zip` asset attached to
the `HI-OLP-PUB-0003` release and Zenodo version DOI
`10.5281/zenodo.21940471`. It contains the relevant append-only decisions,
rejections, source ledger, task history, terminology web, accepted QA,
diagnostic failures and corrections, build products, 300-dpi renders,
publication method, and scripts. Credentials and unrelated corpora are absent.

Prior release receipts remain in `receipts/` as version history; they do not
describe the current 158-file payload.
