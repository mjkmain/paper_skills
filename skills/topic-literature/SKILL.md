---
name: topic-literature
description: "Produce topic-level research deliverables — surveys, briefs, reading lists, research gap reports, and related work sections — from the wiki's synthesized knowledge. Works at the TOPIC level: primary data source is wiki concept pages (already synthesized across papers), not individual paper notes. Use when user says 'write a survey', 'survey on', 'literature survey', 'brief me on', 'what should I read about', 'reading list for', 'write related work', 'position my work', 'what are the gaps', 'research opportunities', 'frontier', 'what's missing', or wants to produce a deliverable document from their accumulated research knowledge. Also trigger when the user wants a structured document about a research topic, asks for a literature review, needs to write a related work section, or wants strategic guidance on what to investigate next."
argument-hint: "[subcommand: survey|brief|reading-list|related-work|gaps] [options]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, Agent
---

# Topic Literature: Produce Deliverables from Research Knowledge

| Field | Value |
|-------|-------|
| **Name** | `topic-literature` |
| **Description** | Produce surveys, briefs, reading lists, related-work sections, and gap reports from the wiki. |
| **Argument** | <code>[subcommand: survey&#124;brief&#124;reading-list&#124;related-work&#124;gaps] [options]</code> |
| **Allowed Tools** | Bash, Read, Write, Edit, Glob, Grep, Agent |
| **Input** | Wiki pages in `./wiki/` (from `paper-wiki`); paper notes as secondary source |
| **Output** | Deliverables in `./wiki/reviews/`, updated `wiki/index.md` and `wiki/log.md` |
| **Prev Skill** | `paper-wiki` — supplies the concept pages, graph, and overview this skill reads from |
| **Loop-Back** | `gaps` subcommand emits copy-pasteable `/paper-collector` queries, closing the pipeline |

Subcommand: **$ARGUMENTS**

## Why This Exists

The wiki accumulates knowledge; this skill produces from it. Concept pages, comparisons, and gap analyses are valuable — but eventually you need a deliverable: a survey for a collaborator, a related work section for your paper, a reading list for a student, a gap analysis to direct your next search. That's what this skill does.

The critical distinction: this skill works at the **topic level**. Its primary data source is wiki concept pages — knowledge already synthesized across multiple papers. Papers appear as evidence within topic-level arguments, not as the unit of organization. A survey section maps to a concept, not to a paper. A reading list follows conceptual progression, not publication dates. Gaps are things a topic lacks, not things a single paper missed.

This is what separates topic-literature from simply re-reading paper notes.

## Role in the Pipeline

```
PAPER LEVEL                              TOPIC LEVEL
paper-collector → paper-reader  →  paper-wiki → topic-literature → DELIVERABLES
                                        ↓               ↓
                                   graph-creator    (gaps → paper-collector)
```

## Prerequisites

This skill reads from the wiki. If `./wiki/` does not exist or is empty, inform the user:
```
No wiki found. Run /paper-wiki init and /paper-wiki build first to create
the knowledge base that topic-literature produces from.
```

## Constants

- **WIKI_DIR = `./wiki/`** — Primary data source. Concept pages, comparisons, overview, graph.
- **NOTES_DIR = `./reference/notes/`** — Secondary data source. Per-paper detail, used for drill-down only.
- **OUTPUT_DIR = `./wiki/reviews/`** — Where deliverables are saved. Create if it doesn't exist.

## Reading Strategy

This is the most important habit for this skill to follow. Start from wiki pages — they contain pre-synthesized topic-level knowledge. Only open individual paper notes when you need:

1. **Specific numbers** — benchmark results, performance comparisons, dataset sizes
2. **Method specifics** — algorithm details not captured in concept page summaries
3. **Citation metadata** — authors, year, venue, arXiv ID for academic-format references

If you find yourself reading many paper notes to write a single survey section, pause and check whether a concept page already covers it. The wiki exists so you don't have to re-derive knowledge from raw notes every time.

## Cross-Cutting Options

| Option | Values | Default | Effect |
|---|---|---|---|
| `-- format:` | `wiki` \| `academic` | varies by subcommand | `wiki`: `[[wikilinks]]` inline. `academic`: `(Author et al., Year)` + reference list |
| `-- save:` | flag | on by default | Persist to `wiki/reviews/`. Pass `-- no-save` to display only |

## Subcommands

---

### `/topic-literature survey "<topic>"`

Produce a comprehensive field survey organized by the topic's internal structure. Default format: `wiki`.

**Options:**
| Option | Values | Default |
|---|---|---|
| `-- scope:` | `narrow` \| `broad` | `broad` |
| `-- max-papers:` | N | all relevant |

`narrow` includes only papers directly tagged with the topic. `broad` also follows one hop in the graph (`extends`, `related_to`, `belongs_to` edges) to pull in contextually relevant work.

**Step 1 — Scope the survey:**

1. Read `wiki/index.md` to find pages related to the topic
2. Read `wiki/overview.md` for field-level context
3. Match concept pages by tag overlap and title similarity to the topic
4. If `broad`: read `graph/edges.jsonl`, include 1-hop neighbor papers
5. Report to user: "Found {N} papers across {M} concepts for '{topic}'"

**Step 2 — Build taxonomy from wiki concepts:**

The taxonomy comes from the wiki's existing concept structure, not from re-analyzing individual papers. This is the core topic-level principle:

1. Read relevant concept pages' **Key Approaches** and **Overview** sections
2. Read comparison pages for already-identified contrasts
3. Organize into a hierarchy by technique, granularity, paradigm, or whatever structure the concept pages reveal
4. Present to user for confirmation — this shapes the entire survey:
   ```
   Proposed taxonomy for "{topic}":
   ├── {Category A} — [[concept-a]] ({N} papers)
   ├── {Category B} — [[concept-b]] ({N} papers)
   └── {Category C} — [[concept-c]] ({N} papers)
   Does this look right?
   ```

**Step 3 — Write the survey:**

Each section draws from specific wiki sources:

```markdown
---
type: review
subtype: survey
topic: "{topic}"
paper_count: {N}
concept_count: {M}
created: {YYYY-MM-DD}
---

# Survey: {Topic}

## 1. Introduction
```
*Source: `overview.md` Field Landscape + concept pages' Overview sections.*
What field is this? Why does it matter? What problem drives the work? End with a roadmap.

```markdown
## 2. Background
```
*Source: foundational concept pages + paper notes' Method sections for key definitions.*
Only what readers need to follow the rest. Keep it concise.

```markdown
## 3. Taxonomy
```
*Source: Step 2 output.*
Present the map. After this section readers should understand the lay of the land.

```markdown
## 4. Detailed Review
### 4.1 {Category A}
### 4.2 {Category B}
```
*Source: concept pages' Key Approaches + Evolution. Paper notes for specific results.*
Each subsection maps to a concept page or cluster. Organize by **approach**, not by paper. "[[rho1]] demonstrated that token-level selection achieves..." is topic-level evidence. "Rho-1 is a paper by Lin et al. that proposes..." is paper-level narration — avoid it.

```markdown
## 5. Comparative Analysis
```
*Source: `wiki/comparisons/` pages + paper notes' Key Results for numbers.*

| Method | Approach | Scale | Key Result | Limitation |
|--------|----------|-------|------------|------------|

What patterns emerge? Where do methods complement each other? Where do they contradict?

```markdown
## 6. Open Problems & Future Directions
```
*Source: concept pages' Open Questions + `overview.md` Research Gaps + paper Limitations.*
Organized by theme, not by paper. Each problem gets: what it is, why it matters, what's been tried.

```markdown
## 7. Conclusion
## References
```

**Step 4 — Save:** Write to `wiki/reviews/survey_{slug}.md`. Append to `wiki/log.md`. Update `wiki/index.md` Reviews section.

---

### `/topic-literature brief "<question>"`

Focused 1-2 page synthesis answering a topic-level question. Default format: `wiki`.

**Options:**
| Option | Values | Default |
|---|---|---|
| `-- depth:` | `quick` \| `thorough` | `quick` |

Briefs answer questions about **topics**: "What's the current state of token-level selection?" or "Is document-level filtering sufficient?" — not about individual papers.

**Workflow:**

1. Read `wiki/index.md` → find relevant concept pages, comparisons, questions
2. Check `wiki/questions/*.md` — if a similar question was already answered via `paper-wiki query --save`, reference it rather than duplicating
3. Read relevant concept pages (primary source)
4. For `thorough`: also read paper notes for specific evidence

**For `quick` (1 page):**

```markdown
---
type: review
subtype: brief
question: "{question}"
depth: quick
created: {YYYY-MM-DD}
---

# {Question}

## Answer
<!-- 2-4 sentences. Take a clear position where evidence supports one. -->

## Evidence
<!-- 3-5 bullets from concept pages and key papers -->
- [[concept-slug]]: {synthesized finding}
- [[short_name]] showed that {specific result} (Year)

## Key References
```

**For `thorough` (2+ pages), add:**

```markdown
## Background
<!-- What you need to know to understand the answer -->

## Detailed Evidence
### {Argument 1}
### {Argument 2}

## Counterarguments & Caveats
<!-- Draw from graph contradicts edges + concept Limitations -->

## Current Consensus

## Open Questions
```

Save to `wiki/reviews/brief_{slug}.md`.

---

### `/topic-literature reading-list "<topic>"`

Curated reading curriculum ordered by **conceptual progression**, not publication date. Default format: `wiki`.

**Options:**
| Option | Values | Default |
|---|---|---|
| `-- audience:` | `beginner` \| `intermediate` \| `expert` | `intermediate` |
| `-- max:` | N | `10` |

**Step 1 — Gather and classify:**

1. Read concept pages related to the topic — their hierarchy defines reading progression
2. Read `graph/edges.jsonl` for paper dependencies (`extends`, `supersedes`, `contradicts`)
3. Read `graph/nodes.jsonl` for metadata

Score each paper:

| Signal | Source | Meaning |
|---|---|---|
| Foundation score | `extends` edges pointing TO this paper | How many papers build on it |
| Centrality | Total edge count | How connected it is |
| Concept membership | `belongs_to` edges | Which topic areas it covers |

Classify into tiers:
- **Foundational** — high foundation score, or defines a core concept
- **Important** — high relevance + centrality, solid read depth available
- **Supplementary** — specialized, tangential, or cutting-edge

**Step 2 — Order by conceptual progression:**

The reading order follows the **topic's conceptual structure**:
1. Papers in foundational concepts come before papers in advanced concepts
2. A paper that is `extended` by others comes before the papers extending it
3. Papers that `supersede` others replace them (note the superseded one as "optional/historical")
4. Within a tier, break ties chronologically

**Audience adjustments:**
- `beginner`: Foundational + important only. Start from the broadest concept's papers. Max 10.
- `intermediate`: All tiers. Start from the concept closest to interest, branch out. 10-15.
- `expert`: Skip obvious foundations (list as "assumed knowledge"). Focus on `emerging`-status concepts, `contradicts` edges (debates), gaps. 8-12.

**Step 3 — Write the reading list:**

```markdown
---
type: review
subtype: reading-list
topic: "{topic}"
audience: "{audience}"
paper_count: {N}
created: {YYYY-MM-DD}
---

# Reading List: {Topic}

> **Audience**: {audience} | **Papers**: {N} | **Est. time**: ~{hours}h
> {What the reader will understand after completing this list.}

## Foundations

### 1. [[short_name]] — {Title}
> **{First Author} et al., {Year}** ({Venue})
> **Why read this**: {2-3 sentences. Be specific: "Introduces selective language
>   modeling — every paper below builds on this concept."}
> **Core idea**: {One sentence}
> **Difficulty**: accessible / moderate / challenging
> **Prerequisites**: none / "paper #N"

## Core Reading

### 3. [[short_name]] — {Title}
> {same format}

## Deep Dives (optional)

### 7. [[short_name]] — {Title}
> {same format}

## Suggested Path

```
1 (foundation)
├── 2 → 3 (extends 2)
│        └── 4 (contrasts with 3 — read both)
└── 5 → 6 (different approach)
         └── 7 (deep dive, optional)
```

"Start with #1 to understand {X}. Then #2 for {Y}. #3 and #4 are
competing approaches — reading both reveals the key debate in this area..."

## Skip If You Already Know...
- Skip #1 if familiar with {concept}
- Skip #2 if you've read {well-known paper}
```

Save to `wiki/reviews/reading-list_{slug}.md`.

---

### `/topic-literature related-work "<focus>"`

Bridge from topic-level knowledge to paper-level academic writing. Default format: `academic`.

This is the one subcommand that produces paper-level output — because academic papers cite papers. But the **organization** still comes from wiki concepts: concept groupings become related-work sections, and the narrative arc traces through concepts toward the user's contribution.

**Options:**
| Option | Values | Default |
|---|---|---|
| `-- contribution:` | string | (asks user) |
| `-- style:` | `narrative` \| `grouped` | `narrative` |
| `-- venue:` | string | none |

If `-- contribution` is not provided, ask — it's essential for positioning:
```
What is your paper's key contribution? This shapes how I position your work.
(e.g., "We propose token-level selection via optimal transport, which
unlike prior methods handles non-stationary distributions")
```

**Venue adaptation:**
| Venue type | Length | References |
|---|---|---|
| Top conference (NeurIPS, ICLR...) | ~1 page | 15-25 |
| Journal | 2-3 pages | 30-50 |
| Workshop | ~0.5 page | 8-12 |
| Default | ~1-1.5 pages | 15-30 |

**Step 1 — Derive groupings from wiki concepts:**

1. Read concept pages relevant to the focus
2. Each concept maps to a related-work paragraph or subsection
3. Order concepts to build a narrative arc toward the user's contribution:
   - Broadest/most established concept first
   - Progress toward concepts closest to the user's work
   - End with the group their work most directly extends

**Step 2 — Write the section:**

For `narrative` (default):
```markdown
**{Concept-derived group.}** {Frame the group.} {Paper A (Author1 et al., Year)}
{1-2 sentences: contribution + limitation the user's work addresses.}
{Paper B (Author2 et al., Year)} {same.} {Transition to what this group leaves unsolved.}

{Repeat for each concept-group.}

In contrast to prior work, our approach {key differentiator}. Unlike
{closest competitor} which {their limitation}, we {user's advantage}.
```

For `grouped`:
```markdown
### 2.1 {Concept-derived group}
{Prose reviewing this thread of work through the concept lens.}

### 2.2 {Next concept-group}

### Discussion
{Positioning: how the user's work fits, differs, extends.}
```

**Step 3 — Generate bibliography** from paper note frontmatter:
```
[1] Lin, Z., Gou, Z., et al. (2024). "Rho-1: Not All Tokens Are What You Need."
    NeurIPS 2024. arXiv: 2404.07965.
```

Save to `wiki/reviews/related-work_{slug}.md`. Note to user: "Review for positioning accuracy and completeness."

---

### `/topic-literature gaps`

Research frontier report — identifies what's missing at the topic level and generates actionable next steps that feed directly back into `paper-collector`. Default format: `wiki`.

**Options:**
| Option | Values | Default |
|---|---|---|
| `-- focus:` | string | all areas |

**Step 1 — Harvest gap signals from topic-level sources:**

| Source | Section | Signal |
|---|---|---|
| `wiki/overview.md` | Research Gaps table | Curated, tracked gaps |
| `wiki/concepts/*.md` | Open Questions | Per-topic unsolved problems |
| `wiki/concepts/*.md` | Strengths & Limitations | Aggregate weaknesses |
| `wiki/graph/edges.jsonl` | `contradicts` edges | Active debates |
| `wiki/graph/nodes.jsonl` | Node counts per concept | Coverage density |
| `reference/notes/*.md` | Limitations | Per-paper signals (secondary) |

**Step 2 — Compile and categorize:**

Deduplicate (same gap from multiple sources). Categorize:

| Category | Meaning |
|---|---|
| **Method gap** | No existing approach addresses this |
| **Scale gap** | Methods exist but untested at scale |
| **Evaluation gap** | No good benchmark or metric |
| **Integration gap** | Two promising approaches never combined |
| **Contradiction** | Papers disagree, unresolved |
| **Coverage gap** | Wiki has thin coverage in this area |

**Step 3 — Prioritize (each axis 1-3):**

- **Impact**: niche (1) → meaningful (2) → field-reshaping (3)
- **Tractability**: needs breakthrough (1) → hard but feasible (2) → clear next step (3)
- **Signal strength**: 1 source (1) → 2-3 sources (2) → widely cited (3)

Sort by total score descending.

**Step 4 — Generate paper-collector commands:**

For each top gap, produce directly copy-pasteable search queries:
```
Gap: "Token-level selection at large scale (>100B tokens)"
  /paper-collector "token-level data selection large scale pretraining" — year: 2024-
  /paper-collector "selective language modeling scaling" — sources: conference
```

**Step 5 — Write the report:**

```markdown
---
type: review
subtype: gaps
focus: "{focus or 'all'}"
gap_count: {N}
created: {YYYY-MM-DD}
---

# Research Gaps & Opportunities

> Analyzed {N} papers across {M} concepts. Wiki last updated: {date}.

## Executive Summary
{3-5 sentences: biggest gaps, most promising directions, immediate actions.}

## Top Opportunities

### G1: {Gap Title} — priority {score}/9
- **Category**: {method / scale / evaluation / integration / contradiction / coverage}
- **Description**: {2-3 sentences}
- **Why it matters**: {impact assessment}
- **Evidence**:
  - [[concept-slug]] Open Questions: "{relevant point}"
  - [[short_name]] Limitations: "{relevant point}"
- **Tractability**: {what it would take to address this}
- **Suggested searches**:
  ```
  /paper-collector "{query}" — year: YYYY-
  /paper-collector "{query}" — sources: conference
  ```

### G2: ...

## Active Debates
| Debate | Position A | Position B | Status |
|--------|-----------|-----------|--------|

## Coverage Gaps
| Area | Papers | Suggested Action |
|------|--------|-----------------|

## Next Actions
1. `/paper-collector "..."` to fill gap G1
2. `/paper-wiki update` to integrate pending papers
3. Investigate {debate} — search for resolution papers
```

Save to `wiki/reviews/gaps_{YYYY-MM-DD}.md`.
Ask: "Want me to update `wiki/overview.md` gaps table or run any of these searches now?"

---

## Citation Engine

Both modes build citations from paper note frontmatter (`title`, `authors`, `year`, `venue`, `arxiv`):

**`format: wiki`** (default for survey, brief, reading-list, gaps):
- Inline: `[[short_name]]`
- First mention in a section can add context: `[[rho1|Rho-1 (Lin et al., 2024)]]`
- No separate reference list — Obsidian resolves links

**`format: academic`** (default for related-work):
- Inline: `(Lin et al., 2024)` or `Lin et al. (2024)` depending on sentence position
- Reference list at end:
  ```
  [1] Lin, Z., Gou, Z., et al. (2024). "Rho-1: Not All Tokens Are What You Need."
      NeurIPS 2024. arXiv: 2404.07965.
  ```

## Next Step

After producing any deliverable, suggest a natural follow-up based on what was made:

- After `survey`, `brief`, or `reading-list` → point at `/topic-literature gaps` to see what the deliverable revealed is missing, and at `/paper-wiki update` if new papers have been read since the wiki was last built.
- After `related-work` → remind the user to sanity-check positioning claims against the actual contribution; suggest `/topic-literature gaps` if they want to strengthen the "what's missing" angle.
- After `gaps` → the report already contains `/paper-collector` queries. Offer to run the top-priority one directly, which restarts the pipeline (`collector → reader → paper-wiki update → topic-literature`).

## Key Rules

- **Wiki first, paper notes second.** Concept pages already synthesize across papers. Drilling into every paper note for a survey defeats the purpose of having the wiki. Use the wiki as your primary source; paper notes are for evidence and specifics.
- **Organize by topic, not by paper.** Survey sections map to concepts. Reading lists follow conceptual progression. Gaps are things a topic lacks. Papers appear as evidence within topic-level arguments.
- **related-work is the one bridge back.** It produces paper-level output because academic norms require it. But even there, the structure — which groups, what order, what narrative — comes from wiki concepts.
- **Save to `wiki/reviews/`.** Outputs belong in the wiki ecosystem. They get indexed, linked with `[[wikilinks]]`, and found in future sessions.
- **Log every output** — append to `wiki/log.md`: `[date] review:{subtype} — {topic}, {N} papers`.
- **Contradictions are strategic intelligence.** Surface them in surveys, briefs, and gap reports. A field where everyone agrees is a field with fewer opportunities.
- **gaps closes the loop.** Its search queries should be directly copy-pasteable into `/paper-collector`. This is how the second brain becomes self-directing.
