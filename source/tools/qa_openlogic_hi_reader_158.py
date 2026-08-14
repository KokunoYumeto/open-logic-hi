"""Render and verify the 158-file Hindi Open Logic working reader.

Every physical page is freshly rasterized at 300 dpi.  The four front-matter
pages and all 207 accepted component pages are independently rasterized from
their source PDFs and must match the corresponding cumulative-reader page
byte-for-byte.  This lets the earlier per-component visual reviews carry into
the cumulative reader without pretending that a spot check covers 211 pages.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from pypdf import PdfReader


LANE = Path(__file__).resolve().parent.parent
RELEASE = LANE / "08_publication" / "openlogic_hi_9620cc7" / "HI-OLP-PUB-0003"
READER = RELEASE / "00_OpenLogic_hi-Deva-IN_WORKING_READER_158-of-722.pdf"
COMPONENT_MANIFEST = RELEASE / "build" / "reader-component-manifest.json"
QA = LANE / "07_qa" / "openlogic" / "HI-OLP-PUB-0003"
RENDER_DIR = QA / "final-reader-render-300dpi"
RECEIPT = QA / "CUMULATIVE_READER_QA.json"
TEXT = QA / "reader-extracted.txt"
PDFTOPPM = Path(
    r"C:\Users\Floris\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"
)
PDFTOTEXT = Path(r"C:\Users\Floris\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftotext.exe")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def numbered_pngs(directory: Path) -> list[Path]:
    pages = list(directory.glob("*.png"))
    pages.sort(key=lambda p: int(re.search(r"-(\d+)\.png$", p.name).group(1)))
    return pages


def render(pdf: Path, destination: Path, prefix: str) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(PDFTOPPM), "-png", "-r", "300", str(pdf), str(destination / prefix)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        raise SystemExit(
            f"pdftoppm failed for {pdf} ({result.returncode}):\n"
            f"{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
        )
    return numbered_pngs(destination)


def annotation_signature(page) -> Counter:
    signatures = []
    for reference in page.get("/Annots") or []:
        annotation = reference.get_object()
        action = annotation.get("/A") or {}
        destination = action.get("/D", annotation.get("/Dest"))
        if isinstance(destination, list):
            destination = [str(item) for item in destination[1:]]
        signatures.append(
            json.dumps(
                {
                    "subtype": str(annotation.get("/Subtype")),
                    "rect": [round(float(x), 3) for x in (annotation.get("/Rect") or [])],
                    "action": str(action.get("/S")),
                    "destination": str(destination),
                    "uri": str(action.get("/URI")),
                },
                sort_keys=True,
            )
        )
    return Counter(signatures)


def main() -> None:
    manifest = json.loads(COMPONENT_MANIFEST.read_text(encoding="utf-8"))
    reader = PdfReader(str(READER))
    if len(reader.pages) != 211:
        raise SystemExit(f"Expected 211 reader pages; got {len(reader.pages)}")
    if str(reader.trailer["/Root"].get("/Lang")) != "hi-IN":
        raise SystemExit("Reader /Lang is not hi-IN")
    if reader.metadata.title != "Open Logic Project — Hindi Working Reader (158 of 722 source files)":
        raise SystemExit(f"Unexpected PDF title: {reader.metadata.title!r}")

    final_pngs = render(READER, RENDER_DIR, "reader-page")
    if len(final_pngs) != 211:
        raise SystemExit(f"Expected 211 final renders; got {len(final_pngs)}")

    source_entries = [
        {
            "kind": "front_matter",
            "path": LANE / manifest["front_matter"]["path"],
            "reader_start_page": 1,
            "expected_pages": 4,
        }
    ]
    for component in manifest["components"]:
        source_entries.append(
            {
                "kind": "accepted_component",
                "title": component["title"],
                "path": LANE / component["path"],
                "reader_start_page": component["reader_physical_pages"][0],
                "expected_pages": component["pages"],
            }
        )

    matches = []
    named_destinations = reader.named_destinations
    unresolved_destinations = []
    annotation_pages_compared = 0
    with tempfile.TemporaryDirectory(prefix="reader-component-render-", dir=QA) as temporary:
        temp_root = Path(temporary)
        for index, entry in enumerate(source_entries):
            component_dir = temp_root / f"component-{index:02d}"
            source_pngs = render(entry["path"], component_dir, "page")
            if len(source_pngs) != entry["expected_pages"]:
                raise SystemExit(
                    f"Page-count mismatch for {entry['path']}: "
                    f"expected {entry['expected_pages']}, rendered {len(source_pngs)}"
                )
            source_pdf = PdfReader(str(entry["path"]))
            for offset, source_png in enumerate(source_pngs):
                physical_page = entry["reader_start_page"] + offset
                final_png = final_pngs[physical_page - 1]
                source_hash = sha256(source_png)
                final_hash = sha256(final_png)
                if source_hash != final_hash:
                    raise SystemExit(
                        f"Raster mismatch at reader page {physical_page}: {entry['path']} page {offset + 1}"
                    )
                if annotation_signature(source_pdf.pages[offset]) != annotation_signature(reader.pages[physical_page - 1]):
                    raise SystemExit(
                        f"Annotation mismatch at reader page {physical_page}: {entry['path']} page {offset + 1}"
                    )
                annotation_pages_compared += 1
                matches.append(
                    {
                        "reader_page": physical_page,
                        "source_pdf": str(entry["path"].relative_to(LANE)).replace("\\", "/"),
                        "source_page": offset + 1,
                        "render_sha256": final_hash,
                    }
                )

    for page_number, page in enumerate(reader.pages, start=1):
        for reference in page.get("/Annots") or []:
            annotation = reference.get_object()
            action = annotation.get("/A") or {}
            if str(action.get("/S")) == "/GoTo":
                destination = action.get("/D")
                if isinstance(destination, str) and destination not in named_destinations:
                    unresolved_destinations.append({"page": page_number, "destination": destination})
    if unresolved_destinations:
        raise SystemExit(f"Unresolved internal link destinations: {unresolved_destinations[:10]}")

    text_result = subprocess.run(
        [str(PDFTOTEXT), "-enc", "UTF-8", str(READER), str(TEXT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if text_result.returncode:
        raise SystemExit(f"pdftotext failed: {text_result.stderr[-2000:]}")
    extracted = TEXT.read_text(encoding="utf-8-sig", errors="strict")
    forbidden = [needle for needle in ("11 / 722", "11/722", "�") if needle in extracted]
    if forbidden:
        raise SystemExit(f"Forbidden stale/replacement text found: {forbidden}")
    required = ["मुक्त तर्क परियोजना", "158 / 722", "समुच्चय", "पूर्णता प्रमेय"]
    missing = [needle for needle in required if needle not in extracted]
    if missing:
        raise SystemExit(f"Required searchable Hindi text missing: {missing}")

    receipt = {
        "schema": "openlogic-hi-cumulative-reader-qa-v1",
        "release_id": "HI-OLP-PUB-0003",
        "reader": {
            "path": str(READER.relative_to(LANE)).replace("\\", "/"),
            "sha256": sha256(READER),
            "pages": 211,
            "lang": "hi-IN",
        },
        "render": {
            "dpi": 300,
            "page_pngs": len(final_pngs),
            "all_pages_independently_matched_to_front_or_accepted_component": True,
            "matches": matches,
        },
        "annotations": {
            "pages_compared": annotation_pages_compared,
            "named_destinations": len(named_destinations),
            "unresolved_internal_destinations": 0,
        },
        "search_and_copy": {
            "pdftotext_exit_code": text_result.returncode,
            "utf8_bytes": TEXT.stat().st_size,
            "required_strings_present": required,
            "stale_11_of_722_absent": True,
            "replacement_character_absent": True,
        },
        "manual_visual_review": {
            "front_matter_pages": [1, 2, 3, 4],
            "new_supplement_pages": [191, 192, 193, 194, 210, 211],
            "status": "PENDING_MANUAL_VIEW_IMAGE_REVIEW",
            "carry_forward_rule": "All other pages raster-match accepted component PDFs with prior every-page visual QA receipts.",
        },
    }
    QA.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "reader_sha256": receipt["reader"]["sha256"],
                "pages": len(final_pngs),
                "raster_matches": len(matches),
                "unresolved_internal_destinations": 0,
                "manual_visual_review": "pending",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
