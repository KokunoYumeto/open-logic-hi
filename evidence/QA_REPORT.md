# QA report — HI-OLP-PUB-0003

Status: **accepted as a machine-assisted Hindi working-reader checkpoint**.

## Scope

- Frozen source: OpenLogicProject/OpenLogic commit
  `9620cc73f9c8e0ad003c514a5d3748f29611c4c0`, tree
  `f67757bb9305b173634082ab4cefd5601a707a34`, CC BY 4.0.
- Target locale: `hi-Deva-IN`.
- Accepted boundary: 158 of 722 source TeX files; 59,955 source words.
- Exact pairs and hashes: `ACCEPTED_FILES.csv`.
- The eight active first-order Semantics files are excluded.

## Reader

- PDF: 211 pages, including 207 translated-content pages.
- Bytes: 3,250,779.
- SHA-256:
  `D08E9EA3D8398DB2A8F3CD3FC966A9849B41549A9282780EE1725B36B1716781`.
- Final assembly preserves 18 accepted compiled components.
- All 211 final pages were freshly rasterized at 300 dpi and matched the
  independently rendered front/component pages byte for byte.
- All internal GoTo destinations resolve: 1,116 named destinations, zero
  unresolved targets.
- Search/copy and required Hindi text probes pass; no replacement character or
  stale `11/722` text occurs.
- `pdffonts` enumerated 281 font-resource rows; every row reports `emb=yes`.
- `/Lang` is `hi-IN`.
- Newly assembled front and boundary pages received direct original-detail
  visual review; the final two-page conjunction defect was rejected, repaired,
  rebuilt, rerendered, and reinspected.

## Audit surface

The GitHub release and exact Zenodo version contain four ordered files: the
reader, editable sources, provenance/QA ZIP, and SHA-256 list. The 416 MB audit
ZIP contains append-only decisions, terminology, source ledgers, failed and
corrected intermediates, build logs, component PDFs, all-page renders, and
publication scripts. The credential value was scanned against both ZIPs and
had zero matches.

## Honest limits

This is not the completed 722-file translation. It is not represented as
human-reviewed, peer-reviewed, a critical edition, or PDF/UA certified.
