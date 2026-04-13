# Paper Skills

Claude Code skills and tools for building a research second-brain. Collect papers, read them, and generate structured knowledge — all from the CLI.

## Pipeline

```
paper-collector          paper-reader            (planned)
   Search & download  -->  Read & digest PDFs  -->  research-wiki
   papers by topic        into structured notes     research-query
                                                    paper-linker
```

All skills share a common workspace: `./reference/` for PDFs, `./reference/notes/` for markdown notes, and `./reference/index.md` as the catalog.

## Skills

### paper-collector

Search, download, and organize research papers by topic.

```
/paper-collector "diffusion models for image generation"
/paper-collector "LLM reasoning" — sources: conference
/paper-collector "neural radiance fields" — sources: conference — year: 2023- — max: 20
```

**Options:**
- `sources: web` (default) — all available sources
- `sources: conference` — top-tier venues only (NeurIPS, ICLR, ICML, ACL, CVPR, etc.)
- `max: N` — limit number of papers (default: 10)
- `year: YYYY-` — filter by year

**Naming convention:** `{year}_{short_name}_{first_author}_{venue}.pdf`
- `short_name` is LLM-generated (e.g. `bert`, `transformer`, `chain_of_thought`)
- Examples: `2017_transformer_vaswani_neurips.pdf`, `2020_ddpm_ho_neurips.pdf`

### paper-reader

Read PDFs from `./reference/` and produce structured markdown notes.

```
/paper-reader all
/paper-reader all — depth: skim
/paper-reader "2024_mamba_gu_icml.pdf" — depth: deep
/paper-reader "transformer" — depth: standard
```

**Depth modes:**

| Depth | Pages read | Use case |
|-------|-----------|----------|
| `skim` | ~5 pages | Triage — decide what's worth a deep read |
| `standard` | ~15 pages | Default — build your knowledge base |
| `deep` | Entire paper | Core papers — detailed method walkthrough |

**Note schema** (written to `./reference/notes/{short_name}.md`):
- TL;DR, Problem & Motivation (5-point structure), Method, Key Results, Strengths, Limitations, Relevance, Key Takeaways
- Deep mode adds: Method Details, Experiments in Detail, Connections, Open Questions

## Tools

Python CLI tools used by the skills. No external dependencies — stdlib only.

| Tool | Purpose | Sources |
|------|---------|---------|
| `arxiv_fetch.py` | Search arXiv, download PDFs, generate filenames | arXiv API |
| `semantic_scholar_fetch.py` | Search published venue papers with citation metadata | Semantic Scholar API |

Both tools output valid JSON (including on errors) and support rate limiting.

```bash
# Search
python3 tools/arxiv_fetch.py search "attention mechanism" --max 10
python3 tools/semantic_scholar_fetch.py search "LLM reasoning" --max 10

# Download
python3 tools/arxiv_fetch.py download 2301.07041 --dir ./reference/

# Generate filename
python3 tools/arxiv_fetch.py make-filename --short-name "bert" --authors "Jacob Devlin" --year 2019 --venue "NAACL"
# -> {"filename": "2019_bert_devlin_naacl.pdf"}
```

## Directory Structure

```
paper_skills/
  skills/
    paper-collector/
      SKILL.md              # Skill definition
    paper-reader/
      SKILL.md              # Skill definition
  tools/
    arxiv_fetch.py           # arXiv search + download + naming
    semantic_scholar_fetch.py # Semantic Scholar API search
```

## Setup

1. Clone this repo
2. Python 3.10+ required
3. (Optional) Set `SEMANTIC_SCHOLAR_API_KEY` for higher rate limits

No `pip install` needed — all tools use Python stdlib only.

## Planned Skills

- **research-wiki** — Build an interlinked wiki from paper notes (following the [LLM-wiki](https://github.com/tobi/llm-wiki) pattern)
- **paper-linker** — Discover relationships between papers, generate a gap map
- **research-query** — Ask questions against the wiki, synthesize answers with citations
