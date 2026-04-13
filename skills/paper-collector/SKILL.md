---
name: paper-collector
description: Search, download, and organize research papers by topic. Use when user says "collect papers", "download papers", "find papers on [topic]", "get papers about [topic]".
argument-hint: [topic] — sources: web|conference — max: N — year: YYYY-
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent
---

# Paper Collector

| Field | Value |
|-------|-------|
| **Name** | `paper-collector` |
| **Description** | Search, download, and organize research papers by topic. |
| **Argument** | `[topic] — sources: web\|conference — max: N — year: YYYY-` |
| **Allowed Tools** | Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent |
| **Output** | PDFs in `./reference/`, updated `./reference/index.md` |
| **Next Skill** | `paper-reader` — generate structured notes from collected papers |

Research topic: $ARGUMENTS

## Constants

- **SAVE_DIR = `./reference/`** — All PDFs are saved here. Fixed path, not configurable.
- **MAX_PAPERS = 10** — Maximum number of papers to download per run
- **NAMING_RULE** — `{year}_{short_name}_{first_author}_{venue}.pdf`
  - `year`: 4-digit publication year (e.g. `2024`)
  - `short_name`: **LLM-generated** iconic short name for the paper — the name researchers actually use to refer to it. This is NOT auto-derived from the title; you (Claude) must decide it using your knowledge of the field.
    - Use the paper's well-known nickname if one exists: `bert`, `gpt4`, `vit`, `clip`, `ddpm`, `nerf`, `llama`, `mamba`
    - If no iconic name, compress the core idea to 1-3 words: `chain_of_thought`, `diffusion_beat_gans`, `flash_attention`, `scaling_laws`
    - Lowercase, underscores between words, no articles/prepositions
  - `first_author`: last name of first author, lowercase (e.g. `vaswani`)
  - `venue`: lowercase venue abbreviation (e.g. `neurips`, `iclr`, `arxiv`). Use `arxiv` for preprints without a venue.
  - Examples:
    - `2017_transformer_vaswani_neurips.pdf`
    - `2019_bert_devlin_naacl.pdf`
    - `2020_ddpm_ho_neurips.pdf`
    - `2021_vit_dosovitskiy_iclr.pdf`
    - `2022_chain_of_thought_wei_neurips.pdf`
    - `2023_llama_touvron_arxiv.pdf`

## Options

Parse `$ARGUMENTS` for these directives:

### `— sources:` (default: `web`)

| Value | Behavior |
|-------|----------|
| `web` | Search all available sources — arXiv, Semantic Scholar, Google Scholar, open web. No venue filtering. This is the **default**. |
| `conference` | **Only** collect papers published at top-tier conferences and journals. Filter results to papers from the following venues (and their workshops): NeurIPS, ICLR, ICML, AAAI, IJCAI, ACL, EMNLP, NAACL, CVPR, ICCV, ECCV, SIGIR, KDD, WWW, CIKM, WSDM, INTERSPEECH, ICASSP, JMLR, TMLR, TACL, IEEE TPAMI, IEEE TNNLS, IEEE TSP. When a paper's venue is unknown or does not match this list, skip it. |

### `— max:` (default: `10`)

Maximum number of papers to download. Override the MAX_PAPERS constant.

### `— year:` (default: none — no year filter)

Year filter for search. Accepts:
- Single year: `2024`
- Range: `2022-2024`
- Open-ended: `2023-` (2023 and later), `-2022` (up to 2022)

> Examples:
> ```
> /paper-collector "diffusion models for image generation"
> /paper-collector "LLM reasoning" — sources: conference
> /paper-collector "neural radiance fields" — sources: conference — year: 2023- — max: 20
> /paper-collector "multimodal learning" — sources: web — year: 2024 — max: 5
> ```

## Top Conference List (for `sources: conference`)

When `sources: conference`, only accept papers whose venue matches one of:

```
ML/AI General:    NeurIPS, ICLR, ICML, AAAI, IJCAI
NLP:              ACL, EMNLP, NAACL, COLING, EACL, TACL
Vision:           CVPR, ICCV, ECCV
Data/IR:          SIGIR, KDD, WWW (TheWebConf), CIKM, WSDM, RecSys
Speech:           INTERSPEECH, ICASSP
Robotics:         RSS, CoRL, ICRA
Systems:          OSDI, SOSP, MLSys
Journals:         JMLR, TMLR, IEEE TPAMI, IEEE TNNLS, IEEE TSP, IJCV
```

Match venue names case-insensitively. Accept common abbreviations and full names (e.g. both "NeurIPS" and "Advances in Neural Information Processing Systems"). Workshop papers from these venues are accepted (e.g. "NeurIPS 2024 Workshop on ...").

## Workflow

### Step 0: Parse Arguments

Extract topic and options (`sources`, `max`, `year`) from `$ARGUMENTS`.

- If no topic is provided, ask the user.
- Apply defaults for any unspecified options.

### Step 1: Scan Existing Collection (`./reference/`)

**This step always runs first.** Before searching online, understand what's already collected.

1. **Check if `./reference/` exists**. If not, create it.
2. **List all PDFs**:
   ```
   Glob: ./reference/**/*.pdf
   ```
3. **Parse filenames**: Since files follow the naming convention `{year}_{short_name}_{first_author}_{venue}.pdf`, extract metadata from filenames to understand the existing collection.
4. **Read `./reference/index.md`** if it exists — this has titles, authors, abstracts for each paper.
5. **Summarize context** to yourself:
   - How many papers are already collected?
   - What topics/venues/years are represented?
   - Which papers are directly related to the current search topic?
6. **Report to user**:
   ```
   ## Existing Collection (./reference/)
   Found {N} papers. {M} appear related to "{topic}":
   - {filename1} — {title}
   - {filename2} — {title}
   ...
   ```
   If the directory is empty, just note "No existing papers found."

> This context informs the search — focus on filling gaps rather than re-downloading what's already there. De-duplicate against existing filenames throughout the workflow.

### Step 2: Search for Papers

Search multiple sources and merge results. De-duplicate by title similarity and arXiv ID.

**Tool paths**: The Python tools live in `paper_skills/tools/` relative to the project root. Locate them once at the start:
```bash
# Resolve tool directory (try common locations)
for d in paper_skills/tools tools; do
  [ -f "$d/arxiv_fetch.py" ] && TOOL_DIR="$d" && break
done
```
If `TOOL_DIR` is unset, fall back to WebSearch for all searches.

**2a. arXiv API search** (always runs):

```bash
python3 "$TOOL_DIR/arxiv_fetch.py" search "QUERY" --max 20
```

If the tool is not found, fall back to WebSearch for arXiv results.

**2b. Semantic Scholar API search** (always runs):

```bash
python3 "$TOOL_DIR/semantic_scholar_fetch.py" search "QUERY" --max 20 \
  --fields-of-study "Computer Science" \
  --open-access
```

If the tool returns an error (e.g. rate limit 429), skip silently and rely on other sources. Both tools always output valid JSON — check the `"error"` field before processing `"data"`.

**2c. WebSearch** (runs when `sources: web`):

```
WebSearch: "QUERY site:arxiv.org OR site:openreview.net OR site:aclanthology.org"
WebSearch: "QUERY research paper PDF"
```

Use WebSearch as a supplementary source to catch papers not indexed by APIs.

**2d. Conference filtering** (when `sources: conference`):

After collecting all candidates, filter to keep only papers whose venue matches the top conference list. Use these signals to determine venue:
1. Semantic Scholar `venue` and `publicationVenue` fields (most reliable)
2. arXiv `comments` field (authors often note "Accepted at NeurIPS 2024")
3. WebSearch snippets mentioning venue
4. If venue cannot be determined, **exclude** the paper

### Step 3: Rank and Select

1. Rank papers by relevance to the query topic
2. Apply year filter if specified
3. Select top N papers (where N = `max` option)
4. Present the selected papers to the user as a table before downloading:

```
| # | Title | Authors | Year | Venue | Source |
|---|-------|---------|------|-------|--------|
```

Ask user to confirm or adjust the selection before proceeding to download.

### Step 4: Download PDFs

For each selected paper, download the PDF:

**4a. Find PDF URL** — try in order:
1. arXiv PDF link: `https://arxiv.org/pdf/{arxiv_id}.pdf`
2. Semantic Scholar `openAccessPdf.url`
3. ACL Anthology PDF link (for ACL/EMNLP/NAACL papers)
4. OpenReview PDF link (for ICLR/NeurIPS papers)
5. WebFetch to find PDF link on the paper's landing page

**4b. Generate filename** using NAMING_RULE:

**You (Claude) must generate the `short_name` yourself.** This is a judgment call, not a mechanical transformation. Think: "What do researchers call this paper?"

```
Input:  "Attention Is All You Need" by Vaswani et al., NeurIPS 2017
Output: 2017_transformer_vaswani_neurips.pdf    (known as "the Transformer paper")

Input:  "BERT: Pre-training of Deep Bidirectional Transformers..." by Devlin et al., NAACL 2019
Output: 2019_bert_devlin_naacl.pdf              (universally called "BERT")

Input:  "Denoising Diffusion Probabilistic Models" by Ho et al., NeurIPS 2020
Output: 2020_ddpm_ho_neurips.pdf                (known as "DDPM")

Input:  "Language Models are Few-Shot Learners" by Brown et al., NeurIPS 2020
Output: 2020_gpt3_brown_neurips.pdf             (known as "GPT-3")

Input:  "Tree of Thoughts: Deliberate Problem Solving with LLMs" by Yao et al., NeurIPS 2023
Output: 2023_tree_of_thoughts_yao_neurips.pdf   (known as "Tree of Thoughts")
```

Guidelines for `short_name`:
- If the paper has a well-known acronym/nickname, use it: `bert`, `gpt3`, `vit`, `clip`, `nerf`
- If not, compress the core contribution to 1-3 words: `flash_attention`, `scaling_laws`, `constitutional_ai`
- Never just truncate the title mechanically — use your understanding of what the paper is about

Then pass the short_name to the tool:
```bash
python3 "$TOOL_DIR/arxiv_fetch.py" make-filename --authors "AUTHORS" --year YEAR --venue "VENUE" --short-name "SHORT_NAME"
```

Venue normalization (handled by tool):
- Map full names to abbreviations: "Advances in Neural Information Processing Systems" → `neurips`
- Unknown venue → `arxiv` for arXiv preprints, `unknown` otherwise
- Lowercase always

**4c. Download and save**:

```bash
# Using arxiv_fetch.py for arXiv papers
python3 "$TOOL_DIR/arxiv_fetch.py" download ARXIV_ID --dir ./reference/

# Then rename to follow naming convention
mv ./reference/ARXIV_ID.pdf ./reference/FILENAME
```

For non-arXiv papers, use WebFetch to download the PDF directly:
```bash
curl -L -o "./reference/FILENAME" "PDF_URL"
```

- Rate limit: 1-second delay between downloads
- Verify each PDF is > 10 KB (reject error pages)
- Skip papers that already exist in ./reference/ (match by filename)

### Step 5: Report

After all downloads complete, present a summary:

```
## Collection Summary

Topic: {topic}
Sources: {web|conference}
Downloaded: {N} papers to ./reference/

| # | Filename | Title | Year | Venue | Size |
|---|----------|-------|------|-------|------|
```

List any papers that failed to download with the reason.

### Step 6: Update Index

**Always run this step.** The index is how `paper-reader` discovers and matches papers by topic. Without it, the reader only has filenames to work with.

If `./reference/index.md` exists, append entries for newly downloaded papers. If it doesn't exist, create it with a header and the entries below:

```markdown
## {Paper Title}
- **File**: {filename}
- **Authors**: {author list}
- **Year**: {year}
- **Venue**: {venue}
- **arXiv**: {arxiv_url or N/A}
- **Abstract**: {first 2 sentences of abstract}
```

De-duplicate: if an entry for the same filename already exists, update it rather than appending a duplicate.

## Next Step

After collection is complete, suggest: "Papers are downloaded. Run `/paper-reader all` to generate structured notes, or `/paper-reader all — depth: skim` for a quick triage pass."

## Key Rules

- **Always confirm** the paper list with the user before downloading
- **Never download** more than MAX_PAPERS in a single run without explicit user approval
- **Rate limit** all downloads — 1 second delay between requests
- **Verify PDFs** — reject files < 10 KB
- **De-duplicate** — skip papers already present in ./reference/
- **Respect naming convention** — every saved PDF must follow NAMING_RULE
- **Graceful degradation** — if a tool is missing, skip that source and continue with others
- Always include arXiv ID or DOI in the index for traceability
