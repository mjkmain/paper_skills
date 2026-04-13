---
name: paper-reader
description: Read and digest research papers from ./reference/, extract key ideas, and produce structured notes. Use when user says "read papers", "summarize papers", "digest papers", "what do these papers say", "make notes from papers".
argument-hint: [filename|topic|"all"] — depth: skim|standard|deep
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, Agent
---

# Paper Reader

| Field | Value |
|-------|-------|
| **Name** | `paper-reader` |
| **Description** | Read and digest research papers, extract key ideas, produce structured notes. |
| **Argument** | `[filename\|topic\|"all"] — depth: skim\|standard\|deep — force: true` |
| **Allowed Tools** | Bash, Read, Write, Edit, Glob, Grep, Agent |
| **Input** | PDFs in `./reference/` (from `paper-collector`) |
| **Output** | Markdown notes in `./reference/notes/`, updated `./reference/index.md` |

Target: $ARGUMENTS

## Pipeline Context

This skill reads PDFs that were collected by `paper-collector`. It expects:
- PDFs in `./reference/` following the naming convention: `{year}_{short_name}_{first_author}_{venue}.pdf`
- An optional `./reference/index.md` with metadata (title, authors, abstract) per paper — created by `paper-collector`

The `short_name` segment of the filename is the canonical identifier used for notes, cross-references, and wikilinks.

## Constants

- **REFERENCE_DIR = `./reference/`** — Where PDFs live (populated by `paper-collector`)
- **NOTES_DIR = `./reference/notes/`** — Where structured notes are written
- **MAX_PAGES_SKIM = 5** — Pages to read in `skim` mode (title, abstract, intro, conclusion)
- **MAX_PAGES_STANDARD = 15** — Pages to read in `standard` mode (above + method + experiments)
- **MAX_PAGES_DEEP = 0** — No limit in `deep` mode (read entire paper)

## Options

Parse `$ARGUMENTS` for these directives:

### Target (required)

What to read. Accepts:
- **A filename**: `2024_mamba_gu_icml.pdf` — read this specific paper
- **A topic**: `"attention mechanisms"` — read all papers in `./reference/` matching this topic
- **`all`** — read every unprocessed paper in `./reference/`

### `— depth:` (default: `standard`)

| Depth | What is read | Output detail | Use case |
|-------|-------------|---------------|----------|
| `skim` | First 5 pages (title, abstract, intro) + last 2 pages (conclusion) | Quick summary: problem, method (1-line), main claim | Triage — deciding what's worth a deep read |
| `standard` | Up to 15 pages (abstract, intro, method, experiments, conclusion) | Full structured note with all fields below | Default — building your knowledge base |
| `deep` | Entire paper, all pages | Everything in `standard` + detailed method walkthrough, equation explanations, per-experiment analysis, limitations, connections to other work | Deep understanding — papers central to your research |

### `— force:` (default: `false`)

When `true`, re-read papers that already have notes in `./reference/notes/`. By default, papers with existing notes are skipped.

> Examples:
> ```
> /paper-reader all
> /paper-reader all — depth: skim
> /paper-reader "2024_mamba_gu_icml.pdf" — depth: deep
> /paper-reader "transformer" — depth: standard
> /paper-reader all — force: true — depth: skim
> ```

## Note Schema

Each paper produces a note at `./reference/notes/{short_name}.md` using this template:

```markdown
---
title: "{full paper title}"
short_name: "{short_name}"
authors: ["{author1}", "{author2}", ...]
year: {year}
venue: "{venue}"
pdf: "../{filename}.pdf"
arxiv: "{arxiv_url or empty}"
date_read: "{YYYY-MM-DD}"
depth: "{skim|standard|deep}"
tags: ["{tag1}", "{tag2}", ...]
---

# {short_name}: {full paper title}

## TL;DR
One sentence. What is this paper about and why does it matter?

## Problem & Motivation
This is the backbone of literature review — understanding *why* a paper exists is more valuable than understanding *what* it does. Cover all five points:

1. **Context**: What is the broader research area and why does it matter?
2. **Specific problem**: What concrete, well-defined problem does this paper tackle?
3. **Why it's hard**: What makes this problem non-trivial? What are the technical challenges?
4. **Prior attempts and their shortcomings**: How have others tried to solve this? Why did those approaches fall short?
5. **The gap**: What specific gap in knowledge or capability does this paper fill?

For `skim` depth: cover at minimum items 1, 2, and 4.

## Method
Core technical contribution. For `skim` depth: 1-2 sentences. For `standard`: a paragraph with key design choices. For `deep`: detailed walkthrough with equations if needed.

## Key Results
Main experimental findings. Numbers, comparisons, benchmarks. Bullet points.

## Strengths
What does this paper do well? (2-3 bullets)

## Limitations
Honest assessment. What's missing, what assumptions are strong, what doesn't generalize? (2-3 bullets)

## Relevance
How does this connect to other papers in ./reference/? What can we reuse or build on?

## Key Takeaways
2-5 bullet points. The things worth remembering a month from now.
```

For `skim` depth: fill TL;DR, Problem & Motivation (at minimum items 1, 2, 4), Method (brief), Key Results (if visible in abstract), and Key Takeaways. For sections you skip, write a single line: `*Skipped — skim depth.*` (not an HTML comment).

For `deep` depth: add these extra sections after Key Takeaways:

```markdown
## Method Details
Detailed walkthrough: architecture, algorithm, loss functions, training procedure. Include key equations in LaTeX if they are central to understanding.

## Experiments in Detail
Per-experiment breakdown: setup, baselines, metrics, results, ablations.

## Connections
Explicit links to other papers in ./reference/notes/. Use wikilink-style: [[short_name]]

## Open Questions
What does this paper leave unanswered? What would you investigate next?
```

**Important**: The template above shows section descriptions as guidance for you (Claude). In the actual output notes, replace every description with real content. Never leave template instructions or HTML comments in the final note.

## Workflow

### Step 1: Scan `./reference/`

1. List all PDFs in `./reference/`:
   ```
   Glob: ./reference/*.pdf
   ```
2. List existing notes:
   ```
   Glob: ./reference/notes/*.md
   ```
3. Determine which papers need reading:
   - If target is `all`: select PDFs without corresponding notes (unless `force: true`)
   - If target is a filename: select that specific PDF
   - If target is a topic: match filenames and (if `index.md` exists) titles/abstracts against the topic
4. Report to user:
   ```
   ## Papers to Read
   Found {N} PDFs in ./reference/, {M} already have notes.
   Will read {K} papers at {depth} depth:
   - {filename1}
   - {filename2}
   ...
   ```

### Step 2: Read Each Paper

For each paper to process:

1. **Read the PDF** using the Read tool:
   - `skim`: read pages 1-5 and the last 2 pages
   - `standard`: read pages 1-15
   - `deep`: read the full PDF (use pages parameter for large PDFs, reading in chunks of ~20 pages)

   **If reading fails** (corrupted PDF, scanned-image-only paper, encoding errors):
   - Try reading just pages 1-3 as a fallback
   - If still unreadable, check `./reference/index.md` for the abstract and write a minimal note with only TL;DR and Problem & Motivation based on the abstract, marking the note with `read_status: "failed"` in frontmatter and a warning: `> Note: PDF could not be fully read. This note is based on metadata only.`
   - Report the failure to the user and continue with the next paper — don't abort the whole batch

2. **Extract metadata** from the PDF content:
   - Title, authors, year, venue (cross-reference with filename)
   - arXiv ID if present

3. **Parse filename** for `short_name`:
   - Filename format: `{year}_{short_name}_{first_author}_{venue}.pdf`
   - Extract `short_name` from the second segment

4. **Generate the structured note** following the Note Schema above. The quality of the note depends entirely on your understanding — read carefully, don't just extract surface-level information.

5. **Generate tags**: Pick 3-7 tags that capture the paper's core topics, methods, and domains. Use lowercase, hyphenated (e.g. `language-models`, `attention`, `reinforcement-learning`). Prefer reusing tags that already appear in existing notes for consistency.

### Step 3: Write Notes

For each paper:

1. Create `./reference/notes/` if it doesn't exist
2. Write the note to `./reference/notes/{short_name}.md`
3. Report progress:
   ```
   Wrote: ./reference/notes/{short_name}.md ({depth} depth)
   ```

### Step 4: Cross-Reference (when reading 2+ papers)

After all individual notes are written:

1. Scan all notes in `./reference/notes/` for potential connections
2. Update the `## Relevance` section of newly created notes to reference related papers using `[[short_name]]` wikilinks
3. If patterns emerge across papers, note them (shared methods, competing approaches, complementary results)

### Step 5: Update Index

Update `./reference/index.md`:
- If it doesn't exist, create it
- For each newly read paper, add or update its entry:

```markdown
### {short_name}
- **Title**: {full title}
- **Authors**: {author list}
- **Year**: {year} | **Venue**: {venue}
- **File**: [{filename}](./{filename})
- **Notes**: [notes/{short_name}.md](./notes/{short_name}.md)
- **Tags**: {tag1}, {tag2}, ...
- **TL;DR**: {one-sentence summary}
```

### Step 6: User Review

**This step always runs.** Present the results for the user to check.

1. **Summary table**:
   ```
   ## Reading Complete

   | # | Paper | Depth | Tags | Note |
   |---|-------|-------|------|------|
   | 1 | {short_name}: {title} | {depth} | {tags} | [view](./reference/notes/{short_name}.md) |
   ```

2. **Quick preview** — for each note, show the TL;DR and Key Takeaways inline so the user can review without opening files:
   ```
   ### {short_name}
   > **TL;DR**: {one-sentence summary}
   >
   > **Key Takeaways**:
   > - {takeaway 1}
   > - {takeaway 2}
   > - ...
   ```

3. **Ask for feedback**:
   ```
   Would you like to:
   - Re-read any paper at a different depth? (e.g. "re-read mamba at deep")
   - Edit any note? (e.g. "edit vit relevance section")
   - Continue to the next step? (e.g. build wiki, link papers)
   ```

   Wait for user response. If the user requests edits, apply them to the note files. If the user wants to re-read at a different depth, go back to Step 2 for that paper with `force: true`.

## Key Rules

- **Read before writing** — never generate a note from metadata alone. Always read the actual PDF content.
- **Be honest** — if a paper's method is unclear after reading, say so in the note. Don't fabricate understanding.
- **Preserve existing notes** — never overwrite existing notes unless `force: true` is set.
- **Consistent tags** — check existing notes for tag vocabulary before inventing new ones.
- **Filename is truth** — derive `short_name` from the PDF filename, not by re-generating it.
- **Respect depth** — don't over-read in `skim` mode (wastes time) or under-read in `deep` mode (misses detail).
- **User review is mandatory** — always present results at the end for the user to verify and adjust.
