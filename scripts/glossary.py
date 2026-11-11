#!/usr/bin/env python3
"""Read the shared DOCX, build a disposable index, and retrieve candidate paragraphs.

No third-party dependencies. Search output is evidence for a human/agent decision,
not a machine-approved bilingual term mapping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "glossary" / "English 0928.docx"
SCHEMA = 2
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HAN = re.compile(r"[\u3400-\u9fff]")
HANS = re.compile(r"[\u3400-\u9fff]+")
LATIN = re.compile(r"[A-Za-z]")
PARENS = re.compile(r"[（(][^）)]*[）)]")


def paragraph_text(p: ET.Element) -> str:
    parts = []
    for el in p.iter():
        if el.tag == NS + "t":
            parts.append(el.text or "")
        elif el.tag == NS + "tab":
            parts.append("\t")
        elif el.tag in (NS + "br", NS + "cr"):
            parts.append("\n")
    return "".join(parts).strip()


def rows_from_docx(path: Path) -> list[dict]:
    try:
        with ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError("Word file cannot be parsed as DOCX") from exc
    body = root.find(NS + "body")
    if body is None:
        raise ValueError("DOCX has no document body")

    rows = []
    section = ""
    paragraph_id = 0
    for block in body:
        if block.tag != NS + "p":
            # A future table is not silently converted into misleading word pairs.
            if block.tag == NS + "tbl":
                rows.append({"id": paragraph_id, "kind": "complex", "section": section,
                             "english": "", "chinese": "", "raw": "[Table: inspect source Word]"})
                paragraph_id += 1
            continue
        raw = paragraph_text(block)
        row_id = paragraph_id
        paragraph_id += 1
        if not raw or re.fullmatch(r"[-—_·.\s]{8,}", raw):
            continue
        style_el = block.find(f"{NS}pPr/{NS}pStyle")
        style = style_el.get(NS + "val", "") if style_el is not None else ""
        has_han = bool(HAN.search(raw))
        has_latin = bool(LATIN.search(raw))
        if style.startswith("Heading") or style in ("1", "2", "3") or (has_han and not has_latin and len(raw) <= 32) or (has_latin and not has_han):
            section = raw
            rows.append({"id": row_id, "kind": "heading", "section": section,
                         "english": "", "chinese": "", "raw": raw})
            continue
        match = HAN.search(raw)
        if match and has_latin and match.start() > 0:
            english = raw[:match.start()].strip(" \t=：:–—-")
            explanation = raw[match.start():].strip()
            base_chinese = PARENS.sub("", explanation).strip()
            # Concatenated bilingual notes and slash alternatives need contextual reading.
            complex_line = bool(re.search(r"[\u3400-\u9fff][A-Za-z]{3,}", base_chinese))
            kind = "complex" if complex_line or len(raw) > 600 else "entry"
            rows.append({"id": row_id, "kind": kind, "section": section,
                         "english": english, "chinese": base_chinese, "raw": raw})
        else:
            rows.append({"id": row_id, "kind": "complex", "section": section,
                         "english": "", "chinese": "", "raw": raw})
    if not rows:
        raise ValueError("DOCX contains no readable paragraphs")
    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_file() -> Path:
    # Cache stays outside the repository and is disposable; path is location-specific.
    location = hashlib.sha256(str(ROOT).encode()).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / "professional-translation-cache" / location / "index.json"


def load_index() -> tuple[dict, bool]:
    if not SOURCE.is_file():
        raise FileNotFoundError("shared glossary is missing: glossary/English 0928.docx")
    digest = sha256(SOURCE)
    cache = cache_file()
    if cache.is_file():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("schema") == SCHEMA and data.get("sha256") == digest and isinstance(data.get("rows"), list):
                return data, False
        except (OSError, ValueError, TypeError):
            pass
    rows = rows_from_docx(SOURCE)
    data = {"schema": SCHEMA, "sha256": digest, "source": "glossary/English 0928.docx",
            "rows": rows, "paragraphs": max(row["id"] for row in rows) + 1}
    cache.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="index-", suffix=".json", dir=cache.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, cache)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return data, True


def compact_han(s: str) -> str:
    return "".join(HANS.findall(s))


def english_tokens(s: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", s.lower().replace("‑", "-").replace("–", "-"))
    # Light plural normalization helps retrieval; the raw source controls the final choice.
    return [t[:-3] + "y" if len(t) > 4 and t.endswith("ies") else
            t[:-1] if len(t) > 4 and t.endswith("s") and not t.endswith("ss") else t
            for t in tokens]


def score(row: dict, query: str, context: str) -> float:
    if row["kind"] == "heading":
        return 0
    raw = row["raw"]
    base_zh = compact_han(row["chinese"])
    q_zh = compact_han(query)
    score_value = 0.0
    if len(q_zh) >= 2:
        if q_zh == base_zh:
            score_value = max(score_value, 110)
        if q_zh in base_zh:
            score_value = max(score_value, 90 + min(len(q_zh), 12))
        if len(base_zh) >= 2 and base_zh in q_zh:
            score_value = max(score_value, 70 + min(len(base_zh), 15))
        if q_zh in compact_han(raw):
            score_value = max(score_value, 45 + min(len(q_zh), 12))
        q_bi = {q_zh[i:i+2] for i in range(len(q_zh)-1)}
        b_bi = {base_zh[i:i+2] for i in range(len(base_zh)-1)}
        overlap = len(q_bi & b_bi)
        if overlap and len(q_zh) > 3:
            score_value = max(score_value, 20 + 25 * overlap / max(len(q_bi), 1))
    q_en = english_tokens(query)
    entry_en = english_tokens(row["english"])
    if q_en and entry_en:
        q_set, e_set = set(q_en), set(entry_en)
        if q_en == entry_en:
            score_value = max(score_value, 110)
        elif len(q_en) > 1 and any(entry_en[i:i + len(q_en)] == q_en for i in range(len(entry_en) - len(q_en) + 1)):
            score_value = max(score_value, 90)
        else:
            overlap = len(q_set & e_set)
            if overlap:
                score_value = max(score_value, 18 + 55 * overlap / max(len(q_set), len(e_set)))
        if len(q_en) == 1 and q_en[0] in entry_en:
            score_value = max(score_value, 60)
    if score_value and context:
        c_zh = compact_han(context)
        c_en = set(english_tokens(context))
        if c_zh and c_zh in compact_han(row["section"] + raw):
            score_value += 5
        if c_en & set(english_tokens(row["section"])):
            score_value += 4
    if row["kind"] == "complex":
        score_value *= 0.8
    return round(score_value, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Check Word hash and refresh index if needed")
    search = sub.add_parser("search", help="Find candidate Word paragraphs")
    search.add_argument("--query", action="append", required=True, help="Repeat for multiple terms")
    search.add_argument("--context", default="", help="Short, nonsensitive domain hint")
    search.add_argument("--limit", type=int, default=6)
    show = sub.add_parser("show", help="Show a paragraph and its neighbors")
    show.add_argument("--id", type=int, required=True)
    show.add_argument("--neighbors", type=int, default=1)
    args = parser.parse_args()
    try:
        data, refreshed = load_index()
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}; no stale index used", file=sys.stderr)
        return 2
    if args.command == "status":
        kinds = {kind: sum(r["kind"] == kind for r in data["rows"]) for kind in ("entry", "complex", "heading")}
        print(json.dumps({"source": data["source"], "sha256": data["sha256"],
                          "paragraphs": data["paragraphs"], "indexed": kinds,
                          "index_refreshed": refreshed}, ensure_ascii=False, indent=2))
    elif args.command == "search":
        if args.limit < 1 or args.limit > 30:
            parser.error("--limit must be between 1 and 30")
        for query in args.query:
            ranked = sorted(((score(row, query, args.context), row) for row in data["rows"]),
                            key=lambda item: (-item[0], item[1]["id"]))
            hits = [{**row, "score": value, "direct_match": value >= 70} for value, row in ranked if value >= 18][:args.limit]
            print(json.dumps({"query": query, "sha256": data["sha256"],
                              "index_refreshed": refreshed, "hits": hits}, ensure_ascii=False, indent=2))
    else:
        rows = [r for r in data["rows"] if abs(r["id"] - args.id) <= max(0, min(args.neighbors, 10))]
        print(json.dumps({"sha256": data["sha256"], "rows": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
