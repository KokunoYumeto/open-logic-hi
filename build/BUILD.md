# Build and verification

The repository fronts the already compiled and verified 211-page reader. Its
SHA-256 must be:

`D08E9EA3D8398DB2A8F3CD3FC966A9849B41549A9282780EE1725B36B1716781`

Run `build.ps1` to verify that reader and the exact 158-file accepted overlay.

For editing or rebuilding chapters, download release file 01. It contains:

- exactly 158 accepted Hindi TeX files;
- the matching 158 frozen English witnesses;
- source/target byte counts and hashes;
- pinned Hindi locale, styles, assets, bibliography, font and licence;
- the standalone wrappers and reader scripts.

Release file 02 contains the actual accepted component PDFs, logs, failure
history, all-page renders, and cumulative QA receipts. The frozen upstream is
OpenLogicProject/OpenLogic commit
`9620cc73f9c8e0ad003c514a5d3748f29611c4c0`. A tranche is accepted only after
its TeX compiles to PDF and the rendered pages are checked.
