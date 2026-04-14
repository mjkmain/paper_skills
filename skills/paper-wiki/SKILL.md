---
name: paper-wiki
description: "Build and maintain a persistent research wiki that synthesizes individual paper notes into an interlinked knowledge base of concept pages, comparisons, and gap analyses. The wiki compounds — every new paper makes it smarter. Use when user says 'build wiki', 'update wiki', 'wiki query', 'lint wiki', 'wiki status', 'synthesize papers', 'what do I know about [topic]', 'add to wiki', 'integrate papers', or wants to turn paper notes into organized, permanent knowledge. Also trigger when the user has just finished reading papers with paper-reader and wants the next step, when they ask about connections between papers, research gaps, or field overviews, or when they want to maintain their research knowledge base."
argument-hint: "[subcommand: init|build|update|query|lint|status] [options]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, Agent
---

# Paper Wiki: Persistent Research Knowledge Base

| Field | Value |
|-------|-------|
| **Name** | `paper-wiki` |
| **Description** | Build and maintain a persistent research wiki from paper notes. |
| **Argument** | <code>[subcommand: init&#124;build&#124;update&#124;query&#124;lint&#124;status] [options]</code> |
| **Allowed Tools** | Bash, Read, Write, Edit, Glob, Grep, Agent |
| **Input** | Paper notes in `./reference/notes/` (from `paper-reader`) |
| **Output** | Wiki pages, graph, and log in `./wiki/` |
| **Prev Skill** | `paper-reader` — supplies the structured notes this skill synthesizes |
| **Next Skill** | `topic-literature` — produce surveys, briefs, and gap reports from the wiki |

Subcommand: **$ARGUMENTS**

## Why This Exists

Individual paper notes (from `paper-reader`) are valuable but isolated. Ask a question that spans five papers and you're re-reading all five notes every time. Nothing compounds.

The wiki solves this by **compiling knowledge once and keeping it current** — concept pages synthesize across papers, the graph tracks relationships, and the overview gives you the big picture at a glance. Every paper you add makes the whole wiki richer, not just one more file in a folder.

This follows the LLM Wiki pattern: you never write the wiki yourself — the LLM writes and maintains all of it. You're in charge of sourcing papers and asking the right questions. The LLM handles summarizing, cross-referencing, and bookkeeping.

## Constants

- **NOTES_DIR = `./reference/notes/`** — Paper-reader output. Read-only for this skill — never modify these files.
- **WIKI_DIR = `./wiki/`** — The wiki. This skill owns this directory entirely.
- **GRAPH_DIR = `./wiki/graph/`** — Relationship graph. Designed for future `graph-creator` skill integration with Graphify/Obsidian.

## Wiki Directory Structure

```
wiki/
  index.md                # Master index of all wiki pages
  log.md                  # Append-only changelog (audit trail)
  overview.md             # Field synthesis + research gaps
  concepts/
    {topic-slug}.md       # Concept synthesis pages (cross-paper)
  comparisons/
    {slug}.md             # Head-to-head method comparisons
  questions/
    {slug}.md             # Filed query answers (knowledge from exploration)
  graph/
    nodes.jsonl           # Node metadata for all entities
    edges.jsonl           # Typed relationships between entities
```

## Subcommands

### `/paper-wiki init`

Create the wiki directory structure.

1. Create `wiki/` and all subdirectories (`concepts/`, `comparisons/`, `questions/`, `graph/`)
2. Create `index.md` with header and empty section stubs
3. Create `log.md` with header
4. Create `overview.md` with the overview template (see Page Schemas)
5. Create empty `graph/nodes.jsonl` and `graph/edges.jsonl`
6. Append to log: `[YYYY-MM-DD HH:MM] init — Wiki initialized`
7. Report to user: structure created, ready for `build`

If `wiki/` already exists, warn the user and ask for confirmation before overwriting.

---

### `/paper-wiki build`

Full build of the wiki from all existing paper notes. Run this the first time, or to rebuild after major changes.

**Step 1: Scan notes**

1. Read all notes from `./reference/notes/*.md`
2. For each note, extract from frontmatter and content:
   - `short_name`, `title`, `authors`, `year`, `venue`, `tags`
   - TL;DR, Problem, Method summary, Key Results, Limitations, Open Questions
3. Report: "Found {N} paper notes. Building wiki..."

**Step 2: Identify concepts**

Concepts are themes, methods, or research areas that span multiple papers. To find them:

1. Collect all tags across papers. Group papers by shared tags.
2. Read each paper's Problem, Method, and Relevance sections for deeper thematic connections beyond tags.
3. Cluster papers into concepts. A concept typically needs 2+ papers, but a single foundational paper can warrant a concept page if it defines a major technique or paradigm.
4. Generate a slug for each concept: lowercase, hyphenated, descriptive (e.g., `data-selection`, `token-level-training`, `loss-reweighting`).

The goal is meaningful groupings that help you think about the field — not one concept per tag. A paper can belong to multiple concepts.

**Step 3: Create concept pages**

For each concept, create `wiki/concepts/{slug}.md` following the Concept Page schema. Read the relevant paper notes carefully. Concept pages should synthesize across papers into a coherent narrative, not list paper summaries one after another.

**Step 4: Identify comparisons**

Look for papers that address the same problem with different approaches. Create comparison pages for significant method contrasts. Not every pair of related papers needs a comparison — focus on cases where the contrast is illuminating.

**Step 5: Build the graph**

Create entries in `graph/nodes.jsonl` for every entity (paper, concept, comparison). Create edges in `graph/edges.jsonl` for all relationships. See Graph Format section below.

**Step 6: Write overview.md**

Synthesize the big picture: What field are these papers in? What are the major themes (link to concept pages)? What gaps exist? What's the frontier? This should read like a mini literature review introduction, not a table of contents.

**Step 7: Write index.md**

Generate a categorical index of all wiki pages:
- **Papers** — alphabetical, with tags and one-line TL;DR
- **Concepts** — with paper count and status
- **Comparisons** — with the papers involved
- **Questions** — if any exist

Each entry links to its page using `[[wikilinks]]`.

**Step 8: Log and report**

Append to `log.md`: build summary with counts.
Report to user: papers processed, concepts created, comparisons created, edge count.

**Suggest next step.** After reporting, point the user at `topic-literature` — the wiki is now ready to produce deliverables:

```
Wiki is built. Next, produce something from it:
  /topic-literature survey "<topic>"       — field survey from concept pages
  /topic-literature brief "<question>"     — focused 1-2 page synthesis
  /topic-literature reading-list "<topic>" — curated reading order
  /topic-literature gaps                   — research gaps + loop-back /paper-collector queries
```

---

### `/paper-wiki update` [short_name]

Incremental update — integrate new papers into the existing wiki. This is the subcommand you'll use most often, whenever `paper-reader` has processed new papers.

- With no argument: auto-detect and integrate all new papers
- With a `short_name`: re-integrate a specific paper (useful after re-reading at deeper depth)

**Step 1: Detect changes**

1. Read `graph/nodes.jsonl` to get papers already in the wiki
2. Scan `./reference/notes/*.md` for all available notes
3. New papers = notes whose `short_name` has no `paper:{short_name}` node in the graph
4. Also check for updated papers: notes with a more recent `date_read` than the node's last-seen date (indicates re-read at deeper depth)
5. Report: "Found {N} new papers to integrate: {list}"

If nothing is new and no specific paper was requested, report "Wiki is up to date" and exit.

**Step 2: Read and analyze**

For each new or updated paper:
1. Read the full note from `./reference/notes/{short_name}.md`
2. Extract metadata, tags, key themes, core contribution
3. Determine which existing concepts this paper relates to (by tag overlap and thematic analysis)
4. Check for contradictions or superseding relationships with existing papers

**Step 3: Integrate into the wiki**

For each paper:

1. **Add to graph** — create/update node in `nodes.jsonl`, add edges to `edges.jsonl`

2. **Update concept pages** — for each concept the paper belongs to:
   - Read the existing concept page
   - Weave the new paper's findings into the existing narrative (do not just append a paragraph at the bottom — integrate it where it fits: in the Overview, Key Approaches, Evolution, etc.)
   - Update frontmatter: `papers` list, `paper_count`, `updated` date

3. **Create new concepts** — if the paper introduces topics not covered by any existing concept page, and those topics are substantial, create new concept pages

4. **Update or create comparisons** — if the paper offers a new approach to a problem already represented in the wiki

5. **Flag contradictions** — if the new paper contradicts findings in existing wiki content, note this explicitly in the relevant concept page and add a `contradicts` edge to the graph. Contradictions are valuable knowledge — don't smooth them over.

**Step 4: Rebuild overview and index**

- Update `overview.md` to reflect the new state (add to Recent Developments, update gaps if addressed)
- Regenerate `index.md`

**Step 5: Log and report**

Append to `log.md`:
```
[YYYY-MM-DD HH:MM] update — Integrated {N} papers: {short_name1}, {short_name2}
  Updated concepts: {list}
  New concepts: {list}
  New edges: {count}
  Contradictions found: {count or "none"}
```

Report to user with a summary. Highlight any contradictions or interesting new connections.

**Suggest next step.** When new papers have been integrated, point the user at `topic-literature` for producing deliverables from the refreshed wiki, or back to `paper-collector` to fill gaps:

```
Wiki updated. Next:
  /topic-literature gaps                    — see what's still missing
  /topic-literature survey "<topic>"        — refresh a survey with new evidence
  /paper-collector "<gap-query>"            — chase a gap surfaced by `gaps`
```

---

### `/paper-wiki query "<question>"` [— save]

Search the wiki and synthesize an answer.

1. **Read `wiki/index.md`** to find relevant pages
2. **Read relevant pages** — concept pages, paper notes, comparisons, overview
3. **Synthesize an answer** — draw from multiple sources, cite with `[[wikilinks]]`
4. Present the answer to the user

If `— save` is specified, file the answer as a permanent wiki page:
- Generate a slug from the question
- Write `wiki/questions/{slug}.md` following the Question Page schema
- Add node and edges to the graph
- Update `index.md`
- Append to `log.md`

Filing good questions back into the wiki is how exploration compounds into permanent knowledge. A comparison you asked about, an analysis, a connection you discovered — these shouldn't vanish into chat history.

---

### `/paper-wiki lint`

Health check the wiki. Report issues and suggest fixes.

Check for:
1. **Orphan papers** — notes in `./reference/notes/` with no corresponding wiki node (need `update`)
2. **Thin concepts** — concept pages with only 1 paper (consider merging or collecting more papers)
3. **Stale overview** — `overview.md` not updated after recent paper additions
4. **Missing connections** — papers sharing 3+ tags but no explicit relationship edge
5. **Empty sections** — wiki pages with unfilled template sections
6. **Broken wikilinks** — `[[references]]` pointing to non-existent pages
7. **Tag drift** — similar tags that should be unified (e.g., `llm` vs `large-language-models`)
8. **Isolated nodes** — graph nodes with zero edges

Output a structured lint report. Ask the user which issues to auto-fix.

---

### `/paper-wiki status`

Quick overview of the wiki state.

```
Paper Wiki Status
──────────────────────────
Papers:      {N} ({new} new since last update)
Concepts:    {N} — {concept1}, {concept2}, ...
Comparisons: {N}
Questions:   {N}
Graph:       {node_count} nodes, {edge_count} edges
Last update: {date from log.md}
──────────────────────────
Coverage: {integrated}/{total_notes} paper notes integrated
```

If coverage < 100%, suggest running `update`.

---

## Page Schemas

### Concept Page (`wiki/concepts/{slug}.md`)

```markdown
---
type: concept
node_id: concept:{slug}
title: "{title}"
aliases: ["{alias1}", "{alias2}"]
tags: [{tag1}, {tag2}]
papers: ["{short_name1}", "{short_name2}"]
paper_count: {N}
status: emerging  # emerging (<3 papers) | active (3-7) | mature (8+)
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
---

# {Title}

## Overview
<!-- Synthesize what this concept is about across ALL linked papers.
     This should read as a coherent narrative, not paper-by-paper summaries. -->

## Key Approaches
<!-- Different methods/paradigms within this concept.
     Organize by approach type, not by paper. Reference papers inline: [[short_name]] -->

## Evolution
<!-- How understanding has developed chronologically.
     Earlier work → recent advances → current frontier -->

## Strengths & Limitations
<!-- Aggregated across papers. What works? What doesn't? -->

## Open Questions
<!-- Unsolved problems, debates, gaps specific to this concept -->

## Connections
<!-- AUTO-GENERATED from graph/edges.jsonl — do not edit manually -->
```

### Comparison Page (`wiki/comparisons/{slug}.md`)

```markdown
---
type: comparison
node_id: comparison:{slug}
title: "{Method A} vs {Method B}"
papers: ["{short_name1}", "{short_name2}"]
tags: [{tag1}]
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
---

# {Method A} vs {Method B}

## Summary
<!-- One paragraph: what is the fundamental difference? -->

## Comparison

| Aspect | {Method A} | {Method B} |
|--------|------------|------------|
| Core idea | ... | ... |
| Strengths | ... | ... |
| Limitations | ... | ... |
| Best for | ... | ... |
| Key result | ... | ... |

## Analysis
<!-- When does each approach shine? Are they complementary or competing? -->

## Connections
<!-- AUTO-GENERATED from graph -->
```

### Question Page (`wiki/questions/{slug}.md`)

```markdown
---
type: question
node_id: question:{slug}
title: "{question}"
tags: [{tag1}]
sources: ["{short_name1}", "{concept_slug}"]
created: {YYYY-MM-DD}
---

# {Question}

## Answer
<!-- Synthesized answer with [[wikilink]] citations -->

## Sources
<!-- Papers and concept pages used to construct this answer -->
```

### Overview Page (`wiki/overview.md`)

```markdown
---
type: overview
paper_count: {N}
concept_count: {N}
updated: {YYYY-MM-DD}
---

# Research Overview

## Field Landscape
<!-- Big picture: what is this research area about? Major threads and relationships. -->

## Key Themes
<!-- 3-7 major themes, each linked to its [[concept-slug]] with 1-2 sentence summary -->

## Research Gaps
| ID | Gap | Related Papers | Status |
|----|-----|---------------|--------|
| G1 | ... | [[paper1]]    | open   |

## Recent Developments
<!-- Papers integrated in the last update cycle -->

## Field Evolution
<!-- Chronological view of how this area has developed -->
```

---

## Graph Format

The graph is stored as two JSONL files. This format is chosen for easy parsing by the future `graph-creator` skill and tools like Graphify, Obsidian graph plugins, or any tool that reads directed graphs.

### `graph/nodes.jsonl`

One JSON object per line. Every entity in the wiki gets a node.

```json
{"id": "paper:rho1", "type": "paper", "label": "Rho-1", "title": "Rho-1: Not All Tokens Are What You Need", "year": 2024, "tags": ["data-selection", "token-weighting"], "file": "reference/notes/rho1.md"}
{"id": "concept:data-selection", "type": "concept", "label": "Data Selection", "title": "Data Selection for LLM Training", "tags": ["data-selection"], "file": "wiki/concepts/data-selection.md"}
{"id": "comparison:rho1-vs-qurating", "type": "comparison", "label": "Rho-1 vs QuRating", "file": "wiki/comparisons/rho1-vs-qurating.md"}
```

Node fields:
- `id` — Canonical ID: `{type}:{slug}`. Used everywhere for cross-referencing.
- `type` — `paper` | `concept` | `comparison` | `question`
- `label` — Short display name for graph visualization
- `title` — Full title
- `year` — (papers only) Publication year, useful for timeline layouts
- `tags` — Array of tags, enables filtering in graph tools
- `file` — Relative path to the wiki/notes page

### `graph/edges.jsonl`

One JSON object per line. Every relationship gets an edge.

```json
{"source": "paper:rho1", "target": "concept:data-selection", "type": "belongs_to"}
{"source": "paper:rho1", "target": "paper:qurating", "type": "related_to", "label": "both address data quality"}
{"source": "paper:dynamic_loss_reweighting", "target": "paper:rho1", "type": "extends", "label": "generalizes token weighting"}
{"source": "paper:rho1", "target": "paper:optimal_control_data_selection", "type": "contradicts", "label": "different stance on token vs example selection"}
```

Edge fields:
- `source`, `target` — Node IDs. Standard graph terminology that maps directly to GEXF, GraphML, D3, and Graphify formats.
- `type` — Relationship type (see below)
- `label` — (optional) Human-readable description for edge labels in visualization

### Edge Types

| Type | From → To | Meaning |
|------|-----------|---------|
| `belongs_to` | paper → concept | Paper contributes to this concept |
| `extends` | paper → paper | Builds on prior work |
| `contradicts` | paper → paper | Disagrees with results or claims |
| `supersedes` | paper → paper | Newer work replaces older |
| `related_to` | any → any | General thematic relationship |
| `compares` | comparison → paper | Comparison page includes this paper |
| `addresses_gap` | paper → overview | Paper addresses a gap listed in overview |
| `derived_from` | question → paper\|concept | Question answer draws from this source |

---

## Key Rules

- **Never modify `./reference/`** — paper notes are owned by `paper-reader`. This skill reads from them, never writes to them.
- **Synthesize, don't concatenate.** Concept pages must read as coherent narratives. "Paper A says X. Paper B says Y." is not synthesis — it's a list wearing a trenchcoat. Weave findings together, highlight agreements and tensions, build a picture of the field.
- **Use `[[wikilinks]]` everywhere.** Link papers by `[[short_name]]`, concepts by `[[concept-slug]]`. This enables Obsidian's graph view and backlink features, and prepares the wiki for Graphify visualization via the future `graph-creator` skill.
- **Graph is the source of truth for relationships.** `## Connections` sections on pages are auto-generated views of `edges.jsonl`. Update the graph first, then regenerate Connections.
- **Contradictions are valuable.** When papers disagree, flag it in concept pages and add `contradicts` edges. Knowing where the field disagrees is as useful as knowing where it agrees.
- **Frontmatter enables tooling.** Every page has YAML frontmatter with `type`, `node_id`, `tags`, dates. This powers Obsidian Dataview queries, graph-creator node styling, and programmatic wiki traversal.
- **Log every mutation.** Every `build`, `update`, `query --save`, and `lint` appends to `log.md`. The log is both an audit trail and a way to track wiki evolution.
- **Confirm destructive operations.** Running `build` on an existing wiki will overwrite content. Always warn before proceeding.
