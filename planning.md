# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**UC Berkeley EECS Professor Reviews and Course Survival Guide**

This domain covers student-generated knowledge about Computer Science and Electrical Engineering courses at UC Berkeley: professor teaching styles, exam difficulty, project time estimates, workload balancing, and research opportunities. This knowledge is valuable because official course catalogs list prerequisites and topics but omit critical student concerns like "how many hours will this project actually take?", "does this professor curve?", or "which two upper divs can I survive together?". Students currently rely on fragmented Reddit threads, word-of-mouth, and Discord messages — this system makes that collective knowledge searchable and attributable.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RateMyProfessors / Reddit | Reviews for John DeNero's CS 61A | `documents/denero_cs61a_reviews.txt` |
| 2 | RateMyProfessors / Discord | Reviews for Joshua Hug's CS 61B | `documents/hug_cs61b_reviews.txt` |
| 3 | Reddit / Student wiki | Reviews for CS 161 (Security) | `documents/cs161_security_reviews.txt` |
| 4 | Student-maintained wiki | Survival guide for CS 170 (Algorithms) | `documents/cs170_algorithms_guide.txt` |
| 5 | Reddit / Piazza | Experiences in CS 188 (AI) | `documents/cs188_ai_experiences.txt` |
| 6 | Student forum / Discord | CS 162 (OS) struggles and tips | `documents/cs162_os_nightmares.txt` |
| 7 | Student wiki | FAQ on getting EECS research positions | `documents/eecs_research_faq.txt` |
| 8 | Reddit thread | Comparison of upper-div workloads | `documents/upperdiv_workload_thread.txt` |
| 9 | Discord / Piazza | CS 61C architecture tips | `documents/cs61c_architecture_tips.txt` |
| 10 | RateMyProfessors / Evals | Reviews for CS 186 (Databases) | `documents/cs186_database_reviews.txt` |
| 11 | Student org notes | Internship recruiting guide | `documents/internship_recruiting_guide.txt` |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 100 characters

**Reasoning:**
The corpus is mixed: short reviews (1-3 paragraphs), longer wiki guides (many sections), and forum threads (scattered comments). A 400-character chunk captures roughly 3-5 sentences — enough for a complete thought (e.g., a single review or a guide subsection) without diluting the embedding with unrelated topics. 100-character overlap ensures that sentences spanning chunk boundaries retain context in at least one adjacent chunk. I chose character-based splitting over token-based because sentence-transformers handles variable tokenization gracefully and character counts are easier to debug when inspecting raw text. For review-heavy documents, 400 characters prevents fragments like "Professor Smith's exams are heavily" while avoiding 600-word chunks that merge unrelated courses.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:**
If deploying for real users with cost not a constraint, I would weigh:
- **Context length:** `all-MiniLM-L6-v2` handles 256 tokens max. For longer guide documents, a model with 512+ token context (e.g., `all-mpnet-base-v2`) would capture more per-chunk context.
- **Accuracy on domain-specific text:** Domain-tuned models (e.g., fine-tuned on academic reviews) might better distinguish between similar course names (CS 170 vs CS 188).
- **Latency:** `all-MiniLM-L6-v2` is optimized for speed (50M parameters). For a real app, I'd benchmark `all-mpnet-base-v2` (110M params) to see if accuracy gains justify 2x embedding latency.
- **Multilingual support:** Not needed here (English-only corpus), but `paraphrase-multilingual-MiniLM-L12-v2` would be required for non-English reviews.

I chose `all-MiniLM-L6-v2` because it runs locally with no API costs, no rate limits, and is the recommended baseline for short English text retrieval.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about DeNero's exam difficulty and grading? | Exams are fair but challenging; midterm average is around 65%; he curves generously; attending lecture matters more than textbook readings. |
| 2 | How many hours should students expect to spend on the Gitlet project in CS 61B? | 40–60 hours; some students spend 40, others up to 60. |
| 3 | What is the recommended maximum number of hard upper-division CS courses per semester? | Maximum 2 hard upper divs per semester; taking 3 (e.g., 170 + 162 + 188) is described as a mistake. |
| 4 | Which CS course involves building a pipelined processor in Logisim? | CS 61C — the third project involves building a pipelined processor. |
| 5 | What do students recommend for securing an EECS research position? | Email professors early (end of freshman/beginning of sophomore year), read their recent papers, attach resume and transcript, apply to 10+ labs, expect 10–15 hours/week commitment. |

---

## Anticipated Challenges

1. **Mixed document structure leading to inconsistent chunks:** The corpus combines short reviews (1 paragraph), long structured guides (10+ paragraphs), and forum threads (scattered usernames and short comments). A fixed 400-character chunk size may split a forum thread mid-comment, producing a fragment like "u/cs_junior_2024: Taking 170 + 162 +" which carries no standalone meaning. This risk is mitigated by the 100-character overlap and by manually inspecting chunks before embedding.

2. **Vocabulary overlap causing off-topic retrieval:** Many documents discuss "projects," "exams," and "Berkeley CS" generally. A query about "CS 61B projects" could retrieve chunks from CS 162 or CS 186 that also mention "projects" and "40 hours," even though the context is wrong. This is a semantic search limitation when documents share high-frequency domain words. I will verify retrieval quality by checking distance scores (targeting <0.5 for top results) and manually inspecting the source metadata of returned chunks.

---

## Architecture

```
+-------------------+     +-------------------+     +-------------------------+
| Document Ingestion| --> |    Chunking       | --> | Embedding + Vector Store|
| (Python stdlib    |     | (custom splitter  |     | (sentence-transformers  |
|  os + pathlib)    |     |  400 chars / 100  |     |  all-MiniLM-L6-v2 +     |
|                   |     |  char overlap)    |     |  ChromaDB HTTP client)  |
+-------------------+     +-------------------+     +-------------------------+
         |                                                    |
         |   .txt files in documents/                         |   metadata: source
         |                                                    |   filename, chunk index
         v                                                    v
+-------------------+     +-------------------+
|    Retrieval      | <-- |    Generation     |
| (ChromaDB query   |     | (Groq llama-3.3   |
|  top-k=5, cosine  |     |  70b-versatile    |
|  similarity)      |     |  grounded prompt) |
+-------------------+     +-------------------+
         |                          |
         |   chunks + scores        |   answer + sources
         v                          v
              +-------------------+
              |   Gradio Web UI   |
              | (Textbox input,   |
              |  Textbox answer,  |
              |  Textbox sources) |
              +-------------------+
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
- **Tool:** Claude (this assistant)
- **Input:** Documents section (10 .txt files, mixed review/guide/thread format), Chunking Strategy section (400 chars / 100 overlap), and architecture diagram.
- **Expected output:** A Python script `ingest.py` with `load_documents()` and `chunk_documents()` functions.
- **Verification:** Run the script, print 5 chunks, and confirm each is readable, self-contained, and carries correct source metadata. Check that total chunk count is between 50 and 2000.

**Milestone 4 — Embedding and retrieval:**
- **Tool:** Claude (this assistant)
- **Input:** Retrieval Approach section (all-MiniLM-L6-v2, top-k=5), architecture diagram, and the output chunk format from Milestone 3.
- **Expected output:** A Python script `embed.py` with `embed_chunks()` and `retrieve(query)` functions using ChromaDB HTTP client.
- **Verification:** Run 3 evaluation queries, inspect returned chunks and distance scores. Confirm top results are relevant and scores are <0.5.

**Milestone 5 — Generation and interface:**
- **Tool:** Claude (this assistant)
- **Input:** Grounding requirement (answer only from retrieved context), output format (answer + programmatic source list), Gradio skeleton from the spec, and Groq API requirements.
- **Expected output:** `app.py` with `ask(query)` function and Gradio Blocks UI. The `ask()` function calls retrieve, formats context, sends to Groq with a strict grounding prompt, and appends sources programmatically.
- **Verification:** Test 2–3 end-to-end queries. Confirm answers cite sources and a question outside the document set receives "I don't have enough information."

