"""Assemble the accepted 158-file Hindi Open Logic working reader.

The component PDFs are immutable accepted build outputs.  This script copies
their pages without scaling, adds a four-page human-facing front matter, and
writes an exact component/page/hash manifest beside the result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


LANE = Path(__file__).resolve().parent.parent
BUILD = LANE / "06_build" / "openlogic_hi_9620cc7"
RELEASE = LANE / "08_publication" / "openlogic_hi_9620cc7" / "HI-OLP-PUB-0003"
FRONT = RELEASE / "build" / "reader-frontmatter.pdf"
OUTPUT = RELEASE / "00_OpenLogic_hi-Deva-IN_WORKING_READER_158-of-722.pdf"
MANIFEST = RELEASE / "build" / "reader-component-manifest.json"

COMPONENTS = [
    ("समुच्चय — Sets", 7, BUILD / "HI-OLP-0047" / "sets.pdf"),
    ("संबंध — Relations", 10, BUILD / "HI-OLP-0049" / "relations-complete.pdf"),
    ("फलन — Functions", 7, BUILD / "HI-OLP-0050" / "functions.pdf"),
    ("समाकृतिक फलन — Isomorphic functions", 1, BUILD / "HI-OLP-0051" / "isomorphic-functions.pdf"),
    ("समुच्चयों का आकार — Size of sets", 15, BUILD / "HI-OLP-0052" / "size-of-sets-complete.pdf"),
    ("अंकगणितीकरण — Arithmetization", 8, BUILD / "HI-OLP-0040" / "arithmetization.pdf"),
    ("अनंत समुच्चय — Infinite sets", 6, BUILD / "HI-OLP-0046" / "infinite.pdf"),
    ("प्रतिज्ञप्ति तर्क: वाक्यविन्यास और अर्थविज्ञान", 7, BUILD / "HI-OLP-0061" / "syntax-and-semantics-build.pdf"),
    ("प्रथम-क्रम तर्क का परिचय", 10, BUILD / "HI-OLP-INT-CHAPTER-0001" / "introduction-build.pdf"),
    ("प्रथम-क्रम तर्क: वाक्यविन्यास", 10, BUILD / "HI-OLP-SYN-CHAPTER-0001" / "syntax-build.pdf"),
    ("निष्पादन-तंत्र — Proof systems", 6, BUILD / "HI-OLP-0067" / "proof-systems-build.pdf"),
    ("अनुक्रम-कलन — Sequent calculus", 15, BUILD / "HI-OLP-0082" / "sequent-calculus-build.pdf"),
    ("स्वाभाविक निगमन — Natural deduction", 14, BUILD / "HI-OLP-0096" / "natural-deduction-build.pdf"),
    ("सत्य-वृक्ष — Tableaux", 14, BUILD / "HI-OLP-TAB-CHAPTER-0001" / "tableaux-build.pdf"),
    ("अभिगृहीतीय निष्पादन — Axiomatic deduction", 14, BUILD / "HI-OLP-AXD-CHAPTER-0001" / "axiomatic-deduction-build.pdf"),
    ("सिद्धता — Provability (supplement)", 1, BUILD / "HI-OLP-PUB-0003" / "extra-provability" / "provability-standalone-build.pdf"),
    ("पूर्णता प्रमेय — Completeness theorem", 12, BUILD / "HI-OLP-COM-CHAPTER-0001" / "completeness-build.pdf"),
    ("अधिकतम संगत समुच्चय — Maximally consistent sets (supplement)", 1, BUILD / "HI-OLP-PUB-0003" / "extra-maximally-consistent-sets" / "maximally-consistent-sets-standalone-build.pdf"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    if not FRONT.is_file():
        raise SystemExit(f"Missing front matter PDF: {FRONT}")
    if sum(item[1] for item in COMPONENTS) != 158:
        raise SystemExit("Component source-file counts do not total 158")

    writer = PdfWriter()
    front_reader = PdfReader(str(FRONT))
    if len(front_reader.pages) != 4:
        raise SystemExit(f"Front matter must be exactly 4 pages, got {len(front_reader.pages)}")
    writer.append(
        front_reader,
        outline_item="मुक्त तर्क परियोजना — हिंदी कार्यशील पाठक",
        import_outline=True,
    )

    manifest_components = []
    physical_page = 5
    for title, source_files, path in COMPONENTS:
        if not path.is_file():
            raise SystemExit(f"Missing accepted component: {path}")
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        start = physical_page
        end = start + page_count - 1
        # Import local named destinations and outlines so chapter-internal
        # navigation survives concatenation.  `outline_item` nests each
        # component's own outline beneath a clear reader-level entry.
        writer.append(reader, outline_item=title, import_outline=True)
        manifest_components.append(
            {
                "title": title,
                "accepted_source_files": source_files,
                "path": str(path.relative_to(LANE)).replace("\\", "/"),
                "sha256": sha256(path),
                "pages": page_count,
                "reader_physical_pages": [start, end],
            }
        )
        physical_page = end + 1

    writer.add_metadata(
        {
            "/Title": "Open Logic Project — Hindi Working Reader (158 of 722 source files)",
            "/Author": "Open Logic Project contributors; Hindi translation prepared at the direction of Floris",
            "/Subject": "Compiled working reader of the accepted Hindi translation",
            "/Keywords": "Hindi, Devanagari, logic, open textbook, translation",
        }
    )
    writer._root_object.update({NameObject("/Lang"): TextStringObject("hi-IN")})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("wb") as handle:
        writer.write(handle)

    output_reader = PdfReader(str(OUTPUT))
    if len(output_reader.pages) != 211:
        raise SystemExit(f"Reader must have 211 pages, got {len(output_reader.pages)}")

    manifest = {
        "schema": "openlogic-hi-working-reader-component-manifest-v1",
        "release_id": "HI-OLP-PUB-0003",
        "locale": "hi-Deva-IN",
        "frozen_source_commit": "9620cc73f9c8e0ad003c514a5d3748f29611c4c0",
        "frozen_source_tree": "f67757bb9305b173634082ab4cefd5601a707a34",
        "accepted_source_files": 158,
        "source_denominator_files": 722,
        "accepted_source_words": 59955,
        "front_matter": {
            "path": str(FRONT.relative_to(LANE)).replace("\\", "/"),
            "sha256": sha256(FRONT),
            "pages": 4,
        },
        "components": manifest_components,
        "reader": {
            "path": str(OUTPUT.relative_to(LANE)).replace("\\", "/"),
            "sha256": sha256(OUTPUT),
            "pages": len(output_reader.pages),
            "translated_content_pages": 207,
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["reader"], ensure_ascii=False))


if __name__ == "__main__":
    main()
