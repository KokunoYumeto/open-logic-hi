#!/usr/bin/env python3
"""Build the human-facing 158-file Open Logic Hindi release packages.

The accepted boundary is derived from byte-level source/target comparison and
an explicit exclusion of the eight active, unaccepted Semantics files.  The
archives are written in a stable order with fixed ZIP timestamps and streamed
from disk so packaging does not create a large in-memory copy.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


LANE = Path(__file__).resolve().parents[1]
WORKSPACE = LANE.parents[4]
SOURCE_ROOT = LANE / "02_source_snapshot" / "openlogic_en_9620cc7" / "content"
TARGET_REPO = LANE / "05_translation" / "openlogic_hi_9620cc7"
TARGET_ROOT = TARGET_REPO / "locale" / "hi" / "content"
PUB = LANE / "08_publication" / "openlogic_hi_9620cc7" / "HI-OLP-PUB-0003"
PUB_BUILD = PUB / "build"
QA_ROOT = LANE / "07_qa"
BUILD_ROOT = LANE / "06_build" / "openlogic_hi_9620cc7"

READER = PUB / "00_OpenLogic_hi-Deva-IN_WORKING_READER_158-of-722.pdf"
EDITABLE_ZIP = PUB / "01_OpenLogic_hi-Deva-IN_EDITABLE_SOURCES_158-of-722.zip"
PROVENANCE_ZIP = PUB / "02_OpenLogic_hi-Deva-IN_PROVENANCE_AND_QA_158-of-722.zip"
CHECKSUMS = PUB / "03_SHA256SUMS.txt"
ACCEPTED_CSV = PUB_BUILD / "ACCEPTED_FILES.csv"
PACKAGE_MANIFEST = PUB_BUILD / "RELEASE_PACKAGE_MANIFEST.json"

ACTIVE_UNACCEPTED = {
    "first-order-logic/syntax-and-semantics/semantics.tex",
    "first-order-logic/syntax-and-semantics/intro-semantics.tex",
    "first-order-logic/syntax-and-semantics/structures.tex",
    "first-order-logic/syntax-and-semantics/covered-structures.tex",
    "first-order-logic/syntax-and-semantics/satisfaction.tex",
    "first-order-logic/syntax-and-semantics/assignments.tex",
    "first-order-logic/syntax-and-semantics/extensionality.tex",
    "first-order-logic/syntax-and-semantics/semantic-notions.tex",
}

EXPECTED_GROUP_COUNTS = {
    "first-order-logic/axiomatic-deduction": 15,
    "first-order-logic/completeness": 13,
    "first-order-logic/introduction": 10,
    "first-order-logic/natural-deduction": 14,
    "first-order-logic/proof-systems": 6,
    "first-order-logic/sequent-calculus": 15,
    "first-order-logic/syntax-and-semantics": 10,
    "first-order-logic/tableaux": 14,
    "propositional-logic/syntax-and-semantics": 7,
    "sets-functions-relations/arithmetization": 8,
    "sets-functions-relations/functions": 8,
    "sets-functions-relations/infinite": 6,
    "sets-functions-relations/relations": 10,
    "sets-functions-relations/sets": 7,
    "sets-functions-relations/size-of-sets": 15,
}

WRAPPERS = [
    "first-order-logic/axiomatic-deduction/provability-standalone-build.tex",
    "first-order-logic/completeness/maximally-consistent-sets-standalone-build.tex",
    "first-order-logic/completeness/maximally-consistent-sets-reference-aliases.aux",
    "sets-functions-relations/functions/isomorphic-functions-build.tex",
]

ACCEPTED_QA_SPECIAL = {
    "HI-OLP-AXD-CHAPTER-0001",
    "HI-OLP-COM-CHAPTER-0001",
    "HI-OLP-INT-CHAPTER-0001",
    "HI-OLP-PUB-0001",
    "HI-OLP-PUB-0002",
    "HI-OLP-SYN-CHAPTER-0001",
    "HI-OLP-TAB-CHAPTER-0001",
}

ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {
    ".aux", ".bib", ".cfg", ".cls", ".csv", ".json", ".jsonl", ".log",
    ".md", ".out", ".sty", ".tex", ".tsv", ".txt", ".yaml", ".yml",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def posix(path: Path) -> str:
    return path.as_posix()


def group_key(rel: str) -> str:
    parts = PurePosixPath(rel).parts
    if len(parts) < 2:
        raise AssertionError(f"Unexpected content path: {rel}")
    return "/".join(parts[:2])


def derive_accepted() -> tuple[list[dict[str, object]], list[str]]:
    source_files = sorted(SOURCE_ROOT.rglob("*.tex"))
    if len(source_files) != 722:
        raise AssertionError(f"Expected 722 frozen source TeX files, found {len(source_files)}")

    changed: list[str] = []
    rows: list[dict[str, object]] = []
    for source in source_files:
        rel = posix(source.relative_to(SOURCE_ROOT))
        target = TARGET_ROOT / Path(rel)
        if not target.is_file():
            continue
        source_hash = sha256(source)
        target_hash = sha256(target)
        if source_hash == target_hash:
            continue
        changed.append(rel)
        if rel in ACTIVE_UNACCEPTED:
            continue
        rows.append(
            {
                "relative_path": rel,
                "source_bytes": source.stat().st_size,
                "source_sha256": source_hash,
                "target_bytes": target.stat().st_size,
                "target_sha256": target_hash,
                "qa_state": "accepted",
            }
        )

    if len(changed) != 166:
        raise AssertionError(f"Expected 166 changed source-mapped files, found {len(changed)}")
    if set(changed).intersection(ACTIVE_UNACCEPTED) != ACTIVE_UNACCEPTED:
        missing = sorted(ACTIVE_UNACCEPTED - set(changed))
        raise AssertionError(f"Active Semantics boundary changed; missing from changed set: {missing}")
    if len(rows) != 158:
        raise AssertionError(f"Expected 158 accepted files, found {len(rows)}")

    counts = Counter(group_key(str(row["relative_path"])) for row in rows)
    if dict(sorted(counts.items())) != dict(sorted(EXPECTED_GROUP_COUNTS.items())):
        raise AssertionError(
            "Accepted group counts differ from certified boundary:\n"
            + json.dumps(dict(sorted(counts.items())), indent=2, ensure_ascii=False)
        )
    return rows, changed


def write_csv(rows: list[dict[str, object]]) -> None:
    ACCEPTED_CSV.parent.mkdir(parents=True, exist_ok=True)
    with ACCEPTED_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def zip_info(arcname: str, mode: int = 0o644) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(arcname, date_time=ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (mode & 0xFFFF) << 16
    info.create_system = 3
    return info


def add_file(zf: zipfile.ZipFile, source: Path, arcname: str) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    arcname = PurePosixPath(arcname).as_posix()
    with source.open("rb") as src, zf.open(zip_info(arcname), "w") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)


def add_tree(
    zf: zipfile.ZipFile,
    source_root: Path,
    archive_root: str,
    *,
    exclude=None,
) -> int:
    count = 0
    if not source_root.exists():
        return 0
    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        rel = source.relative_to(source_root)
        if exclude is not None and exclude(source, rel):
            continue
        add_file(zf, source, f"{archive_root}/{posix(rel)}")
        count += 1
    return count


def write_editable_zip(rows: list[dict[str, object]]) -> int:
    members = 0
    with zipfile.ZipFile(EDITABLE_ZIP, "w", allowZip64=True, compresslevel=9) as zf:
        add_file(zf, PUB_BUILD / "EDITABLE_SOURCES_README.md", "README_FIRST.md")
        add_file(zf, ACCEPTED_CSV, "ACCEPTED_FILES.csv")
        members += 2

        for row in rows:
            rel = str(row["relative_path"])
            add_file(zf, SOURCE_ROOT / Path(rel), f"source/content/{rel}")
            add_file(zf, TARGET_ROOT / Path(rel), f"target/locale/hi/content/{rel}")
            members += 2

        for dirname in ("assets", "bib", "include", "sty"):
            members += add_tree(
                zf,
                TARGET_REPO / dirname,
                f"build-support/{dirname}",
                exclude=lambda _source, rel: any(part == ".git" for part in rel.parts),
            )

        members += add_tree(
            zf,
            TARGET_REPO / "locale" / "hi",
            "build-support/locale/hi",
            exclude=lambda _source, rel: rel.parts and rel.parts[0] == "content",
        )

        for root_name in (
            "LICENSE.md",
            "README.md",
            "Makefile",
            "open-logic-complete-config.sty",
            "open-logic-complete.tex",
            "open-logic-config.sty",
            "open-logic-debug.tex",
            "open-logic-envs.sty",
            "open-logic-locale.sty",
        ):
            source = TARGET_REPO / root_name
            add_file(zf, source, f"build-support/{root_name}")
            members += 1

        for wrapper in WRAPPERS:
            add_file(zf, TARGET_ROOT / Path(wrapper), f"wrappers/{wrapper}")
            members += 1

        add_file(zf, PUB_BUILD / "reader-frontmatter.tex", "publication/reader-frontmatter.tex")
        members += 1
        for tool_name in (
            "assemble_openlogic_hi_reader_158.py",
            "qa_openlogic_hi_reader_158.py",
            "package_openlogic_hi_release_158.py",
        ):
            add_file(zf, LANE / "tools" / tool_name, f"tools/{tool_name}")
            members += 1
    return members


def accepted_numeric_qa(name: str) -> bool:
    prefix = "HI-OLP-"
    if not name.startswith(prefix):
        return False
    tail = name[len(prefix):]
    return len(tail) == 4 and tail.isdigit() and 1 <= int(tail) <= 98


def publication_history_exclude(source: Path, _rel: Path) -> bool:
    return source.suffix.lower() in {".zip", ".pdf"}


def general_secret_exclude(source: Path, rel: Path) -> bool:
    lowered = "/".join(part.lower() for part in rel.parts)
    if any(term in lowered for term in ("api_token", "access_token", "credential", "secret", ".env")):
        return True
    if any(part.lower() in {"token", "token.txt", "token.md", "zenodo token.md"} for part in rel.parts):
        return True
    return source.suffix.lower() in {".zip"}


def write_provenance_zip(rows: list[dict[str, object]]) -> int:
    del rows  # boundary is represented by the generated CSV
    members = 0
    component_manifest = json.loads((PUB_BUILD / "reader-component-manifest.json").read_text("utf-8"))

    with zipfile.ZipFile(PROVENANCE_ZIP, "w", allowZip64=True, compresslevel=6) as zf:
        add_file(zf, PUB_BUILD / "PROVENANCE_README.md", "README_FIRST.md")
        add_file(zf, ACCEPTED_CSV, "accepted/ACCEPTED_FILES.csv")
        members += 2

        for name in (
            "reader-component-manifest.json",
            "assembly-console.txt",
            "reader-frontmatter.tex",
            "reader-frontmatter.log",
        ):
            add_file(zf, PUB_BUILD / name, f"publication/{name}")
            members += 1

        members += add_tree(zf, LANE / "00_lane_control", "lane-control", exclude=general_secret_exclude)
        members += add_tree(zf, LANE / "04_terminology", "terminology", exclude=general_secret_exclude)
        members += add_tree(zf, LANE / "03_census" / "openlogic", "source-census/openlogic", exclude=general_secret_exclude)

        openlogic_qa = QA_ROOT / "openlogic"
        for qa_dir in sorted(path for path in openlogic_qa.iterdir() if path.is_dir()):
            name = qa_dir.name
            if name == "HI-OLP-PUB-0003":
                continue
            if not (accepted_numeric_qa(name) or name in ACCEPTED_QA_SPECIAL):
                continue
            exclude = publication_history_exclude if name in {"HI-OLP-PUB-0001", "HI-OLP-PUB-0002"} else general_secret_exclude
            members += add_tree(zf, qa_dir, f"qa/accepted/{name}", exclude=exclude)

        members += add_tree(
            zf,
            openlogic_qa / "HI-OLP-PUB-0003",
            "qa/current",
            exclude=general_secret_exclude,
        )
        members += add_tree(zf, QA_ROOT / "failures", "qa/failures", exclude=general_secret_exclude)

        component_dirs: set[Path] = set()
        for component in component_manifest["components"]:
            component_path = LANE / Path(component["path"])
            component_dirs.add(component_path.parent)
        for component_dir in sorted(component_dirs):
            rel = component_dir.relative_to(BUILD_ROOT)
            members += add_tree(
                zf,
                component_dir,
                f"builds/components/{posix(rel)}",
                exclude=general_secret_exclude,
            )

        methodology = WORKSPACE / "methodology" / "multilingual-publication-datacite-zenodo-github"
        members += add_tree(
            zf,
            methodology,
            "publication-methodology",
            exclude=general_secret_exclude,
        )

        for tool in sorted((LANE / "tools").glob("*openlogic*")):
            if tool.is_file():
                add_file(zf, tool, f"tools/{tool.name}")
                members += 1

    return members


def verify_zip(path: Path, *, required: set[str]) -> dict[str, object]:
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise AssertionError(f"Duplicate archive members in {path.name}")
        missing = required - set(names)
        if missing:
            raise AssertionError(f"Missing required members in {path.name}: {sorted(missing)}")
        bad = zf.testzip()
        if bad is not None:
            raise AssertionError(f"CRC failure in {path.name}: {bad}")
        suspicious = []
        for name in names:
            lowered = name.lower()
            parts = PurePosixPath(lowered).parts
            if any(term in lowered for term in ("api_token", "access_token", "credential", "secret", ".env")):
                suspicious.append(name)
            elif any(part in {"token", "token.txt", "token.md", "zenodo token.md"} for part in parts):
                suspicious.append(name)
        if suspicious:
            raise AssertionError(f"Credential-like archive member names in {path.name}: {suspicious}")
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "members": len(names),
    }


def main() -> int:
    if not READER.is_file():
        raise FileNotFoundError(READER)
    if sha256(READER) != "D08E9EA3D8398DB2A8F3CD3FC966A9849B41549A9282780EE1725B36B1716781":
        raise AssertionError("Reader hash differs from the cumulative QA-certified artifact")

    rows, changed = derive_accepted()
    write_csv(rows)

    editable_members = write_editable_zip(rows)
    provenance_members = write_provenance_zip(rows)

    editable = verify_zip(
        EDITABLE_ZIP,
        required={
            "README_FIRST.md",
            "ACCEPTED_FILES.csv",
            "publication/reader-frontmatter.tex",
        },
    )
    provenance = verify_zip(
        PROVENANCE_ZIP,
        required={
            "README_FIRST.md",
            "accepted/ACCEPTED_FILES.csv",
            "publication/reader-component-manifest.json",
            "qa/current/CUMULATIVE_READER_QA.json",
            "qa/current/MANUAL_VISUAL_REVIEW.md",
        },
    )
    if editable["members"] != editable_members or provenance["members"] != provenance_members:
        raise AssertionError("Archive member accounting mismatch")

    reader_entry = {
        "name": READER.name,
        "bytes": READER.stat().st_size,
        "sha256": sha256(READER),
        "pages": 211,
    }
    assets = [reader_entry, editable, provenance]
    CHECKSUMS.write_text(
        "".join(f'{asset["sha256"]}  {asset["name"]}\n' for asset in assets),
        encoding="ascii",
        newline="\n",
    )
    checksum_entry = {
        "name": CHECKSUMS.name,
        "bytes": CHECKSUMS.stat().st_size,
        "sha256": sha256(CHECKSUMS),
    }
    manifest = {
        "schema": "openlogic-hi-release-package-manifest-v1",
        "release_id": "HI-OLP-PUB-0003",
        "locale": "hi-Deva-IN",
        "frozen_source_commit": "9620cc73f9c8e0ad003c514a5d3748f29611c4c0",
        "frozen_source_tree": "f67757bb9305b173634082ab4cefd5601a707a34",
        "source_denominator_files": 722,
        "changed_source_mapped_files": len(changed),
        "accepted_files": len(rows),
        "active_unaccepted_files_excluded": sorted(ACTIVE_UNACCEPTED),
        "accepted_source_words": 59955,
        "assets": assets + [checksum_entry],
    }
    PACKAGE_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PACKAGE FAILURE: {exc}", file=sys.stderr)
        raise
