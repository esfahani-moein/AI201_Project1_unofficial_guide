# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**UC Berkeley EECS Professor Reviews and Course Survival Guide**

This system covers student-generated knowledge about UC Berkeley Computer Science and Electrical Engineering courses: professor teaching styles, exam difficulty and curves, project time estimates, workload balancing strategies, and research opportunities. This knowledge is valuable because official course catalogs list prerequisites and topics but omit the information students actually need to plan their semesters — like how many hours a project takes, whether a professor curves generously, or which two upper-division courses can be taken together without burnout. Students currently rely on fragmented Reddit threads, Discord messages, and word-of-mouth. This RAG system makes that collective knowledge searchable, answerable, and attributable.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors / Reddit | Professor reviews | `documents/denero_cs61a_reviews.txt` |
| 2 | RateMyProfessors / Discord | Professor reviews | `documents/hug_cs61b_reviews.txt` |
| 3 | Reddit / Student wiki | Course reviews | `documents/cs161_security_reviews.txt` |
| 4 | Student-maintained wiki | Survival guide | `documents/cs170_algorithms_guide.txt` |
| 5 | Reddit / Piazza | Course experiences | `documents/cs188_ai_experiences.txt` |
| 6 | Student forum / Discord | Course struggles & tips | `documents/cs162_os_nightmares.txt` |
| 7 | Student wiki | FAQ | `documents/eecs_research_faq.txt` |
| 8 | Reddit thread | Workload comparison | `documents/upperdiv_workload_thread.txt` |
| 9 | Discord / Piazza | Architecture tips | `documents/cs61c_architecture_tips.txt` |
| 10 | RateMyProfessors / Evals | Course reviews | `documents/cs186_database_reviews.txt` |
| 11 | Student org notes | Recruiting guide | `documents/internship_recruiting_guide.txt` |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 100 characters

**Why these choices fit your documents:**
The corpus is mixed: short reviews (1-3 paragraphs), longer wiki guides (many sections), and forum threads (scattered comments). A 400-character chunk captures roughly 3-5 sentences — enough for a complete thought (e.g., a single review or a guide subsection) without diluting the embedding with unrelated topics. 100-character overlap ensures that sentences spanning chunk boundaries retain context in at least one adjacent chunk. I chose character-based splitting over token-based because sentence-transformers handles variable tokenization gracefully and character counts are easier to debug when inspecting raw text. For review-heavy documents, 400 characters prevents fragments while avoiding chunks so large that specific queries can't match precisely.

Preprocessing before chunking: stripped excessive whitespace and blank lines, but preserved all substantive text including source headers. No HTML cleaning was needed since documents were plain .txt files.

**Final chunk count:** 89 chunks across 11 documents

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Production tradeoff reflection:**
I chose `all-MiniLM-L6-v2` because it runs locally with no API costs, no rate limits, and is the recommended baseline for short English text retrieval. If deploying for real users with cost not a constraint, I would weigh:
- **Context length:** `all-MiniLM-L6-v2` handles 256 tokens max. For longer guide documents, a model with 512+ token context (e.g., `all-mpnet-base-v2`) would capture more per-chunk context.
- **Accuracy on domain-specific text:** Domain-tuned models (e.g., fine-tuned on academic reviews) might better distinguish between similar course names (CS 170 vs CS 188).
- **Latency:** `all-MiniLM-L6-v2` is optimized for speed (50M parameters). For a real app, I'd benchmark `all-mpnet-base-v2` (110M params) to see if accuracy gains justify 2x embedding latency.
- **Multilingual support:** Not needed here (English-only corpus), but `paraphrase-multilingual-MiniLM-L12-v2` would be required for non-English reviews.

---

## Grounded Generation

**System prompt grounding instruction:**
The system prompt is explicit and imperative:

```
You are "The Unofficial Guide," a helpful assistant that answers questions about UC Berkeley EECS courses and professors using ONLY the student-generated documents provided below.

Rules:
1. Answer using ONLY the information in the provided documents.
2. If the documents do not contain enough information to answer the question, say exactly: "I don't have enough information on that."
3. Cite the source document name(s) in your answer using the format [source: filename.txt].
4. Do not use outside knowledge, generalizations, or assumptions.
5. Be concise but specific.
```

The retrieved chunks are injected directly into the prompt under a `Documents:` header, so the LLM has no external context to draw from. Temperature is set to 0.2 to reduce hallucination. The instruction "say exactly: 'I don't have enough information on that.'" is a hard constraint rather than a suggestion.

**How source attribution is surfaced in the response:**
Source attribution is guaranteed programmatically. The UI displays two text boxes: "Answer" and "Retrieved from." The "Retrieved from" box lists every source document that was retrieved for the query, regardless of whether the LLM cited it in its prose. This ensures the user always knows which documents the answer was drawn from, even if the LLM omits a citation. Additionally, the system prompt explicitly instructs the LLM to cite sources in [source: filename.txt] format.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about DeNero's exam difficulty and grading? | Exams are fair but challenging; midterm average around 65%; curves generously; class curved to B+; attending lecture matters more than textbook. | "fair but challenging," tests conceptual understanding; midterm average ~65%, curves generously; class curved to B+ average; exams have code-tracing questions; do past exams [source: denero_cs61a_reviews.txt] | Relevant | Accurate |
| 2 | How many hours should students expect to spend on the Gitlet project in CS 61B? | 40-60 hours; some spend 40, others up to 60. | Around 20-25 hours per week on Gitlet/BearMaps [source: upperdiv_workload_thread.txt], or specifically for Gitlet around 40+ hours [source: hug_cs61b_reviews.txt]. | Partially relevant | Partially accurate |
| 3 | What is the recommended maximum number of hard upper-division CS courses per semester? | Maximum 2 hard upper divs per semester; taking 3 (e.g., 170 + 162 + 188) is described as a mistake. | "I don't have enough information on that." | Partially relevant | Inaccurate |
| 4 | Which CS course involves building a pipelined processor in Logisim? | CS 61C — the third project involves building a pipelined processor. | CS 61C — Great Ideas in Computer Architecture and Machine Structures [source: cs61c_architecture_tips.txt]. | Relevant | Accurate |
| 5 | What do students recommend for securing an EECS research position? | Email professors early, read recent papers, attach resume and transcript, apply to 10+ labs, expect 10-15 hrs/week. | Start with research areas page, narrow to 2-3 fields, read recent papers, email professors with specific references, attach materials [source: eecs_research_faq.txt]. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**
"What is the recommended maximum number of hard upper-division CS courses per semester?"

**What the system returned:**
"I don't have enough information on that."

**Root cause (tied to a specific pipeline stage):**
The failure occurred at the **chunking stage**. The key sentence — "Taking 170 + 162 + 188 together was the worst decision of my academic career... Max 2 hard upper divs per semester." — was split across a chunk boundary in `upperdiv_workload_thread.txt`. The first half of the sentence ended at the boundary of chunk #0, and the second half began chunk #1. Although 100-character overlap should have preserved it, the chunk breaker logic in `ingest.py` prioritized breaking at a newline before checking space boundaries. Because the forum thread had irregular formatting with usernames and line breaks, the critical phrase was fragmented. The retrieval stage did return a chunk from `upperdiv_workload_thread.txt` (score 0.472), but that chunk started mid-sentence with "divs per semester. u/graduated_2023..." and did not contain the standalone instruction "Max 2 hard upper divs per semester." Without a self-contained chunk containing that fact, the generation stage correctly concluded it lacked sufficient information.

**What you would change to fix it:**
I would switch to a sentence-aware chunking strategy (e.g., split on sentence boundaries using `nltk` or a regex, then group sentences into ~400-character chunks) rather than fixed-character splitting. This would preserve the integrity of declarative sentences like "Max 2 hard upper divs per semester." Alternatively, I would increase the overlap to 150-200 characters for forum-thread documents to ensure split sentences are fully captured in adjacent chunks.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The spec's Chunking Strategy section forced me to justify a specific chunk size before writing code. I committed to 400 characters with 100-character overlap based on the mixed document structure (reviews + guides + threads). Having this number written down prevented me from constantly second-guessing myself during implementation. When I encountered the failure case in Q3, I could trace it directly back to the chunking spec rather than guessing whether retrieval or generation was at fault.

**One way your implementation diverged from the spec, and why:**
The spec originally assumed cosine distance scores below 0.5 would be easy to achieve. In practice, ChromaDB defaulted to L2 distance, producing scores around 0.8-1.1 that were unintuitive. I diverged by explicitly setting `metadata={"hnsw:space": "cosine"}` in the ChromaDB collection configuration so that scores would map to the expected [0, 1] range. This wasn't in the original spec because I hadn't anticipated the distance metric mismatch between sentence-transformers (cosine-similarity-oriented) and ChromaDB's default L2 indexing.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* I gave Claude my Chunking Strategy section from planning.md (400 chars / 100 overlap) and my Documents section describing the mixed review/guide/thread corpus, and asked it to implement `ingest.py` with `load_documents()` and `chunk_documents()`.
- *What it produced:* Claude produced a `chunk_text()` function using a simple fixed-character split with a basic word-boundary fallback that only checked for spaces, not newlines.
- *What I changed or overrode:* I modified the chunking logic to prioritize splitting at newlines over spaces, since my forum-thread documents had username prefixes on separate lines that created natural semantic boundaries. I also added an empty-chunk filter (`[c for c in chunks if c]`) because the initial implementation produced zero-length strings when overlap equaled chunk size at document boundaries.

**Instance 2**

- *What I gave the AI:* I gave Claude my Retrieval Approach section (all-MiniLM-L6-v2, top-k=5, ChromaDB HTTP client), my architecture diagram, and the expected chunk format from Milestone 3. I asked for `embed.py` with `embed_chunks()` and `retrieve(query)`.
- *What it produced:* Claude generated embedding and retrieval code using ChromaDB's persistent local client (`chromadb.PersistentClient`), which would write to a local `.chroma` directory.
- *What I changed or overrode:* I overrode the client to `chromadb.HttpClient(host="localhost", port=8000)` because the project infrastructure already provided a running ChromaDB Docker container on port 8000. Using the local persistent client would have bypassed the shared container and created a separate, non-persistent database. I also added cosine distance configuration (`metadata={"hnsw:space": "cosine"}`) after noticing the default L2 distances were unintuitive.
