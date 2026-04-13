#!/usr/bin/env python3
"""CLI helper for searching and downloading arXiv papers.

Used by the ``paper-collector`` skill (skills/paper-collector/SKILL.md).

Commands
--------
search    Search arXiv and print results as JSON.
download  Download a paper PDF by arXiv ID.
rename    Rename a downloaded PDF using the standard naming convention.

Naming convention: {year}_{short_name}_{first_author}_{venue}.pdf
The short_name is provided by the caller (LLM-generated), NOT auto-derived.

Examples
--------
python3 tools/arxiv_fetch.py search "attention mechanism" --max 10
python3 tools/arxiv_fetch.py search "id:2301.07041" --max 1
python3 tools/arxiv_fetch.py download 2301.07041 --dir papers
python3 tools/arxiv_fetch.py download 2301.07041 --dir papers --rename --short-name "transformer"
python3 tools/arxiv_fetch.py make-filename --title "Attention Is All You Need" --authors "Vaswani" --year 2017 --venue "NeurIPS" --short-name "transformer"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

_ATOM_NS = "http://www.w3.org/2005/Atom"
_API_BASE = "http://export.arxiv.org/api/query"
_USER_AGENT = "paper-collector/1.0"
_MIN_PDF_BYTES = 10_240
_NEW_STYLE_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
_OLD_STYLE_ID_RE = re.compile(r"^[A-Za-z.-]+/\d{7}(v\d+)?$")

# Venue name normalization map
_VENUE_MAP = {
    "advances in neural information processing systems": "neurips",
    "neurips": "neurips",
    "nips": "neurips",
    "international conference on learning representations": "iclr",
    "iclr": "iclr",
    "international conference on machine learning": "icml",
    "icml": "icml",
    "association for computational linguistics": "acl",
    "acl": "acl",
    "empirical methods in natural language processing": "emnlp",
    "emnlp": "emnlp",
    "north american chapter of the association for computational linguistics": "naacl",
    "naacl": "naacl",
    "conference on computer vision and pattern recognition": "cvpr",
    "cvpr": "cvpr",
    "international conference on computer vision": "iccv",
    "iccv": "iccv",
    "european conference on computer vision": "eccv",
    "eccv": "eccv",
    "aaai conference on artificial intelligence": "aaai",
    "aaai": "aaai",
    "international joint conference on artificial intelligence": "ijcai",
    "ijcai": "ijcai",
    "sigir": "sigir",
    "kdd": "kdd",
    "the web conference": "www",
    "www": "www",
    "thewebconf": "www",
    "cikm": "cikm",
    "wsdm": "wsdm",
    "recsys": "recsys",
    "interspeech": "interspeech",
    "icassp": "icassp",
    "robotics: science and systems": "rss",
    "rss": "rss",
    "conference on robot learning": "corl",
    "corl": "corl",
    "icra": "icra",
    "jmlr": "jmlr",
    "journal of machine learning research": "jmlr",
    "tmlr": "tmlr",
    "transactions on machine learning research": "tmlr",
    "ieee transactions on pattern analysis and machine intelligence": "tpami",
    "tpami": "tpami",
    "ieee tpami": "tpami",
    "ieee transactions on neural networks and learning systems": "tnnls",
    "tnnls": "tnnls",
    "ieee tnnls": "tnnls",
    "ieee transactions on signal processing": "tsp",
    "tsp": "tsp",
    "ieee tsp": "tsp",
    "tacl": "tacl",
    "transactions of the association for computational linguistics": "tacl",
    "international journal of computer vision": "ijcv",
    "ijcv": "ijcv",
    "coling": "coling",
    "eacl": "eacl",
    "osdi": "osdi",
    "sosp": "sosp",
    "mlsys": "mlsys",
    "openreview": "openreview",
}


def _normalize_id(arxiv_id: str) -> str:
    """Strip URL/version noise and return a clean arXiv ID."""
    value = arxiv_id.strip()
    if "/abs/" in value:
        value = value.split("/abs/", 1)[1]
    if value.startswith("id:"):
        value = value[3:]
    if "v" in value.split(".")[-1]:
        value = value.rsplit("v", 1)[0]
    return value


def _looks_like_arxiv_id(value: str) -> bool:
    """Return True when the input resembles a modern or legacy arXiv ID."""
    value = value.strip()
    return bool(_NEW_STYLE_ID_RE.match(value) or _OLD_STYLE_ID_RE.match(value))


def _api_url(query: str, max_results: int, start: int) -> str:
    """Build the arXiv API URL for a search query or specific ID lookup."""
    query = query.strip()
    if query.startswith("id:"):
        params = {"id_list": _normalize_id(query)}
    elif _looks_like_arxiv_id(query):
        params = {"id_list": _normalize_id(query)}
    else:
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    return f"{_API_BASE}?{urllib.parse.urlencode(params)}"


def _fetch_atom(url: str) -> ET.Element:
    """Fetch an arXiv Atom feed and return the parsed XML root."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return ET.fromstring(resp.read())


def _parse_entry(entry: ET.Element) -> dict:
    """Extract structured fields from a single Atom <entry> element."""
    raw_id = entry.findtext(f"{{{_ATOM_NS}}}id", "")
    arxiv_id = _normalize_id(raw_id)
    title = (entry.findtext(f"{{{_ATOM_NS}}}title", "") or "").strip().replace("\n", " ")
    abstract = (entry.findtext(f"{{{_ATOM_NS}}}summary", "") or "").strip().replace("\n", " ")
    published = (entry.findtext(f"{{{_ATOM_NS}}}published", "") or "")[:10]
    updated = (entry.findtext(f"{{{_ATOM_NS}}}updated", "") or "")[:10]
    authors = [
        author.findtext(f"{{{_ATOM_NS}}}name", "")
        for author in entry.findall(f"{{{_ATOM_NS}}}author")
    ]
    categories = [
        category.get("term", "")
        for category in entry.findall(f"{{{_ATOM_NS}}}category")
        if category.get("term")
    ]
    # Check comments for venue info (authors often write "Accepted at NeurIPS 2024")
    comment = ""
    for link in entry.findall(f"{{{_ATOM_NS}}}link"):
        pass  # links don't have comments
    # arXiv comment field is in arxiv namespace
    arxiv_ns = "http://arxiv.org/schemas/atom"
    comment_el = entry.find(f"{{{arxiv_ns}}}comment")
    if comment_el is not None and comment_el.text:
        comment = comment_el.text.strip()

    return {
        "id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "updated": updated,
        "categories": categories,
        "comment": comment,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
    }


def sanitize_short_name(short_name: str) -> str:
    """Sanitize an LLM-provided short name for use in filenames.

    The short_name is generated by the LLM (e.g. "bert", "chain_of_thought",
    "gpt3"). This function just cleans it for filesystem safety.
    """
    text = unicodedata.normalize("NFKD", short_name).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9_]", "_", text.lower().strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "untitled"


def normalize_venue(venue: str | None, comment: str = "") -> str:
    """Normalize venue name to a short abbreviation.

    Checks both the venue field and arXiv comment for conference mentions.
    Returns 'arxiv' if no venue can be determined.
    """
    # Try venue field first
    if venue:
        key = venue.strip().lower()
        # Direct match
        if key in _VENUE_MAP:
            return _VENUE_MAP[key]
        # Partial match — check if any known venue name is in the string
        for pattern, abbrev in _VENUE_MAP.items():
            if pattern in key:
                return abbrev

    # Try extracting venue from arXiv comment (e.g. "Accepted at NeurIPS 2024")
    if comment:
        comment_lower = comment.lower()
        for pattern, abbrev in _VENUE_MAP.items():
            if pattern in comment_lower:
                return abbrev

    return "arxiv"


def make_filename(
    short_name: str,
    authors: list[str],
    year: str | int | None,
    venue: str | None = None,
    comment: str = "",
) -> str:
    """Generate a filename following the naming convention.

    Format: {year}_{short_name}_{first_author}_{venue}.pdf

    The short_name is provided by the caller (LLM-generated), e.g. "bert",
    "transformer", "chain_of_thought". This function sanitizes it and
    assembles the full filename.
    """
    # Year
    yr = str(year)[:4] if year else "unknown"

    # Short name (LLM-provided, just sanitize)
    clean_short = sanitize_short_name(short_name)

    # First author last name
    if authors:
        first_author = authors[0].strip().split()[-1].lower()
        first_author = unicodedata.normalize("NFKD", first_author).encode("ascii", "ignore").decode()
        first_author = re.sub(r"[^a-z]", "", first_author)
    else:
        first_author = "unknown"

    # Venue
    venue_abbrev = normalize_venue(venue, comment)

    return f"{yr}_{clean_short}_{first_author}_{venue_abbrev}.pdf"


def search(query: str, max_results: int = 10, start: int = 0) -> list[dict]:
    """Search arXiv and return a list of paper dictionaries."""
    url = _api_url(query, max_results=max_results, start=start)
    root = _fetch_atom(url)
    return [_parse_entry(entry) for entry in root.findall(f"{{{_ATOM_NS}}}entry")]


def download(
    arxiv_id: str,
    output_dir: str = "papers",
    rename: bool = False,
    short_name: str | None = None,
) -> dict:
    """Download a paper PDF and return metadata about the saved file.

    If rename=True and short_name is provided, saves the file using the
    naming convention: {year}_{short_name}_{first_author}_{venue}.pdf
    The short_name must be provided by the caller (LLM-generated).
    """
    clean_id = _normalize_id(arxiv_id)
    safe_id = clean_id.replace("/", "_")

    dest_dir = Path(output_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # First download to a temp name
    temp_dest = dest_dir / f"{safe_id}.pdf"

    if temp_dest.exists() and not rename:
        return {
            "id": clean_id,
            "path": str(temp_dest),
            "size_kb": temp_dest.stat().st_size // 1024,
            "skipped": True,
        }

    # Download the PDF
    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    req = urllib.request.Request(pdf_url, headers={"User-Agent": _USER_AGENT})

    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 1:
                time.sleep(5)
                continue
            raise
    else:
        raise RuntimeError(f"Failed to download {pdf_url} after retries")

    if len(data) < _MIN_PDF_BYTES:
        raise ValueError(
            f"Downloaded file is only {len(data)} bytes - likely an error page, not a PDF"
        )

    temp_dest.write_bytes(data)

    result = {
        "id": clean_id,
        "path": str(temp_dest),
        "size_kb": len(data) // 1024,
        "skipped": False,
    }

    # Rename if requested (requires short_name from the LLM)
    if rename and short_name:
        papers = search(f"id:{clean_id}", max_results=1)
        if papers:
            paper = papers[0]
            filename = make_filename(
                short_name=short_name,
                authors=paper["authors"],
                year=paper["published"][:4] if paper.get("published") else None,
                venue=None,
                comment=paper.get("comment", ""),
            )
            final_dest = dest_dir / filename
            if final_dest.exists():
                temp_dest.unlink()
                result["path"] = str(final_dest)
                result["skipped"] = True
                result["filename"] = filename
            else:
                temp_dest.rename(final_dest)
                result["path"] = str(final_dest)
                result["filename"] = filename

    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and download arXiv papers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search arXiv papers")
    search_parser.add_argument(
        "query",
        help="Search query or arXiv ID (bare ID or id:ARXIV_ID).",
    )
    search_parser.add_argument(
        "--max",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of results (default: 10).",
    )
    search_parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start offset for pagination (default: 0).",
    )

    download_parser = subparsers.add_parser("download", help="Download a paper PDF by arXiv ID")
    download_parser.add_argument(
        "id",
        help="arXiv paper ID, e.g. 2301.07041 or cs/0601001",
    )
    download_parser.add_argument(
        "--dir",
        default="papers",
        metavar="DIR",
        help="Output directory (default: papers).",
    )
    download_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to sleep after download (default: 1.0).",
    )
    download_parser.add_argument(
        "--rename",
        action="store_true",
        default=False,
        help="Rename downloaded PDF using naming convention (requires --short-name).",
    )
    download_parser.add_argument(
        "--short-name",
        default=None,
        help="LLM-generated short name for the paper (e.g. 'bert', 'transformer').",
    )

    rename_parser = subparsers.add_parser(
        "make-filename",
        help="Generate a filename from paper metadata (no download)",
    )
    rename_parser.add_argument("--short-name", required=True, help="LLM-generated short name (e.g. 'bert', 'vit')")
    rename_parser.add_argument("--authors", required=True, help="Comma-separated author names")
    rename_parser.add_argument("--year", required=True, help="Publication year")
    rename_parser.add_argument("--venue", default=None, help="Venue name")
    rename_parser.add_argument("--comment", default="", help="arXiv comment field")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.command == "search":
            results = search(args.query, max_results=args.max, start=args.start)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return 0

        if args.command == "download":
            result = download(args.id, output_dir=args.dir, rename=args.rename, short_name=args.short_name)
            if result.get("skipped"):
                print(json.dumps({**result, "message": "already exists, skipped"}, ensure_ascii=False))
            else:
                time.sleep(args.delay)
                print(json.dumps(result, ensure_ascii=False))
            return 0

        if args.command == "make-filename":
            authors = [a.strip() for a in args.authors.split(",")]
            filename = make_filename(
                short_name=args.short_name,
                authors=authors,
                year=args.year,
                venue=args.venue,
                comment=args.comment,
            )
            print(json.dumps({"filename": filename}, ensure_ascii=False))
            return 0

        raise ValueError(f"Unsupported command: {args.command}")

    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted", "data": []}, ensure_ascii=False))
        return 130
    except Exception as exc:
        # Always output valid JSON so the caller can parse it safely
        print(json.dumps({"error": str(exc), "data": []}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
