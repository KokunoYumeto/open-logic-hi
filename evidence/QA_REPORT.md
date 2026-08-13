# QA report — HI-OLP-PUB-0002

Status: **accepted as a machine-assisted cumulative working-reader release**.

## Scope and identity

- Source: OpenLogicProject/OpenLogic commit
  `9620cc73f9c8e0ad003c514a5d3748f29611c4c0`, tree
  `f67757bb9305b173634082ab4cefd5601a707a34`, CC BY 4.0.
- Target locale: `hi-Deva-IN`.
- Included bounded units: `HI-OLP-0001` through `HI-OLP-0011`.
- Coverage: 11 accepted source files; source TeXcount 5,369; Hindi target
  TeXcount 7,276. This is not a whole-work completion claim.
- Exact continuation cursor: `content/sets-functions-relations/relations/trees.tex`,
  stable ID `sfr/rel/tre`, 5,232 bytes, TeXcount 685, SHA-256
  `57CC56EE55506AA19E7BE6129D2CAD6B8635FD2D6407399D4F774782F2CDD588`.

## Final build

- Wrapper: 3,466 bytes; SHA-256
  `8B0BE182362D1E557A23A8AC45F26EDC45DB99B320CEBECD1CB7DF69FE5BDAD1`.
- Final build: two successful XeLaTeX XDV passes followed by successful
  `xdvipdfmx` conversion.
- Hard-error/box/missing-glyph/reference scan: 0 hits.
- Build log: 87,043 bytes; SHA-256
  `A31C789BF849750FE7DCA290881924E526546E3BEE2E8AA15C83A347FB14C343`.
- XDV: 437,612 bytes; SHA-256
  `F6C835F20906CD01A125704EED9A9E34CA9BC052E85B8D0BB2EEC6E955127526`.
- PDF: 17 pages; 212,719 bytes; SHA-256
  `BC7D4F6280D2E3DA427715B7CA2DF5335E8057AD0C0DCBCADEF8C18E27360468`.

## Text, fonts, and visual review

- Every included source unit passed its own literal command, environment,
  stable-ID, label, mathematical-context, build, extraction, font, rendered-page,
  and independent replay checks before admission.
- Poppler layout extraction produced 49,268 characters, zero replacement
  characters, passed 11/11 positive Hindi section probes, and found none of
  the 11 corresponding English source titles. Extraction SHA-256:
  `342BD029D5D4515A17C2B3CFEA188EA3DC4593729EBA5C69C42DF24027B1678F`.
- PDF catalogue language is `/Lang hi-IN`.
- `pdffonts`: 18/18 instances embedded, subset, and Unicode-mapped; all 5
  Devanagari instances are Unicode-mapped.
- All 17 final pages were rendered at 300 dpi and opened at original detail.
  Review found no clipping, overlap, missing/tofu glyphs, broken formula or
  diagram, unintended blank page, or footer/page-number collision. Render
  manifest SHA-256:
  `64E7A65A847957C10A654D2ECC46F9BD4A039D4E0326A386F29CCEE17EC60AD3`.

## Repaired and retained defects

- A cumulative-only 10.4039 pt overfull box in the orders unit was repaired by
  a narrowly scoped `sloppypar`; the individual accepted unit remained intact.
- The first 17-page reader used the descriptive disk job name in the footer,
  crowding page 11's number. That PDF (215,268 bytes; SHA-256
  `07802438F6207AB2FE437D677426C951848E06AEA256B5D2FA56F0EB5B81D153`)
  was rejected. Its 17 original-detail renders remain under
  `render_300dpi_rejected_long_footer/`. The final wrapper uses the linked,
  compact display label `OpenLogic-hi` while retaining the CC BY link.
- One malformed PowerShell `latexmk` argument created a literal `$out`
  scratch directory; it was identified, bounded to the wrapper directory, and
  removed. A second `latexmk` attempt unnecessarily invoked BibTeX and returned
  nonzero because its out-of-tree bibliography paths were not resolvable.
  Neither invocation is accepted build evidence. The final direct XeLaTeX/XDV
  toolchain returned zero and produced the accepted PDF above.

## Honest limitations

- The reader is cumulative through 11 units, not the complete Open Logic work.
- No human linguistic review is claimed or required as a production gate.
- The PDF is untagged: it has no structure tree, marked-content declaration,
  or `ActualText` objects and is not certified as PDF/UA.
- Poppler search/copy extraction passes. pypdf extracts nonempty text from all
  pages but splits many Devanagari clusters, so only 3/11 exact Hindi probes
  match there. This tool divergence is retained in `PYPDF_CHECKS.json`.

Machine outputs, page hashes, every render, the rejected-render evidence, and
the check script are retained beside this report.
