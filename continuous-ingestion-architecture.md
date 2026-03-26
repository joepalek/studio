# Continuous Data Ingestion Architecture
## The Homogenization Pipeline
## Captured 2026-03-26

---

## Core Philosophy

Two types of data — never mix them:

### Type A — Voice/Character Data (how humans EXPRESS themselves)
Sources: Books, old internet (pre-2008), Wayback long-form, 
         Usenet, early forums, BBS archives, personal homepages,
         mailing lists, early blogs, academic discussions
         
Rule: NO post-2010 internet for character voice.
Why: Post-2010 is compressed, SEO-optimized, engagement-optimized,
     written knowing AI might read it. It produces AI-sounding characters.

### Type B — Context/Fact Data (what is TRUE right now)
Sources: Current web, APIs, databases, news, eBay sold data,
         WorthPoint, current collector sites, Wikipedia current
         
Rule: Use ONLY for factual grounding, pricing, current events.
Why: Characters need to know facts from their era but also need
     to be able to reference current context when relevant.

Characters trained on Type A + updated with Type B =
humans who happen to know current facts, not AIs pretending to be humans.

---

## The 5 Output Streams

Every piece of ingested data gets tagged and routed to one or more:

### Stream 1 — eBay Lookup Data
Tags: item identification, collector vocabulary, pattern names,
      maker marks, era-specific terminology, pricing history,
      authentication tells, reproduction flags
Fed by: Collector forums, replacement sites, hallmark databases,
        trade catalogs, early eBay community boards
Format: JSON per item category with confidence scores
Used by: eBay Identifier consensus engine (Track 4 — Archive Historian)

### Stream 2 — Era Specific Data  
Tags: decade, cultural context, slang, technology available,
      prices of common items, media references, political context,
      what people worried about, what they aspired to
Fed by: Decade-specific Wayback snapshots, Vintage Agent profiles,
        newspaper archives, Usenet by year, GeoCities era sites
Format: Per-decade JSON profiles (already started in vintage-agent)
Used by: Vintage Agent, CTW character system, Ghost Book era verification

### Stream 3 — Expert Knowledge Data
Tags: domain, expertise level, pre-Wikipedia, peer-reviewed context,
      methodology, technical depth, minority positions
Fed by: University extension pages, trade association archives,
        early expert homepages, technical mailing lists,
        pre-SEO how-to content, early Stack Overflow equivalent forums
Format: Tagged knowledge chunks with source credibility score
Used by: Ghost Book validator, eBay Identifier, Patent Archaeology

### Stream 4 — Project Idea Data
Tags: market gap, failed product, unbuilt patent, abandoned project,
      premature technology, consumer complaint, underserved niche
Fed by: Product Archaeology (Reddit/HN/old forums), Patent archives,
        Wayback dead product sites, C2C AM fringe ideas,
        early web startup graveyards
Format: Scored idea entries feeding whiteboard.json
Used by: Whiteboard Agent, Market Intelligence Agent

### Stream 5 — Character Voice Data
Tags: decade, social class, region, education level, domain expertise,
      emotional register, sentence complexity, vocabulary range,
      how they argue, how they explain, how they ask questions
Fed by: Books (Project Gutenberg + archive.org), Usenet by topic/year,
        Early personal homepages, mailing list threads,
        BBS conversations, long-form forum debates,
        Academic correspondence archives
Format: Voice corpus per persona type, indexed by era + class + domain
Used by: CTW character system, AI author agents, dialogue generators

---

## The Ingestion Pipeline

### Stage 1 — Discovery (Weekly)
- CDX API broad scan for new targets by category
- Domain classification (forum/expert/personal/commercial)
- Era detection from URL patterns, content, metadata
- Queue building for fetch stage

### Stage 2 — Fetch (Daily delta)
- Pull new/changed content from queued targets
- Rate-limited (respect archive.org limits)
- Raw HTML → cleaned text via existing scraper_utils.py
- Deduplication against existing corpus

### Stage 3 — Process (Daily, Gemini/Ollama)
- Extract structured data per stream type
- Tag with era, domain, credibility score
- Thread reconstruction for forum content
- Vocabulary frequency analysis
- Noise filtering (ads, navigation, boilerplate)

### Stage 4 — Homogenize (Weekly)
- Merge new data into existing stream files
- Resolve contradictions (newer expert consensus wins)
- Cross-reference streams (same fact appearing in multiple = higher confidence)
- Update indices

### Stage 5 — Distribute (On demand / scheduled)
- Push relevant chunks to each project that uses them
- Update studio-context.md with new data summaries
- Flag high-value finds for inbox review
- Score new ideas and push to whiteboard.json

---

## What Makes This Different From Normal Scraping

Normal scraping: grab content, store it, search it.

This pipeline: grab content, understand WHAT KIND OF HUMAN WROTE IT,
tag it for PURPOSE, route it to the right knowledge base,
make it queryable by era + voice + domain + credibility.

The output isn't a search index. It's a CHARACTER LIBRARY.
Each entry knows: who would have written this, when, why, 
and what they were trying to say.

---

## Scheduling

Daily:
- 02:00 — Fetch delta (new content from queued targets)
- 03:00 — Process raw fetches through Gemini/Ollama
- 04:00 — Distribute to project streams

Weekly:
- Monday 01:00 — Vintage Agent / era data pass
- Wednesday 01:30 — Ghost Book / expert data pass  
- Sunday 02:00 — Full CDX discovery scan for new targets
- Sunday 03:00 — Homogenize all streams

---

## Priority Build Order

1. Stream 2 (Era Data) — Vintage Agent already started, extend it
2. Stream 1 (eBay Lookup) — Directly accelerates income now
3. Stream 5 (Character Voice) — CTW needs this, STA needs this
4. Stream 3 (Expert Knowledge) — Ghost Book, eBay Identifier
5. Stream 4 (Project Ideas) — Already partially running via Product Archaeology

---

## The Long Game

This corpus, properly built and tagged, becomes:
- A fine-tuning dataset for era-specific voice models
- A collector knowledge base (licensable)
- A historical language corpus (academic value)
- A character development resource (productizable)
- An AI training dataset filling a known gap in current LLMs

The infrastructure to build it costs near-zero.
The data itself, once structured, has real market value.

---

## Project Status
- Status: WHITEBOARD — CDX infrastructure exists, pipeline not built
- Priority: HIGH (feeds 6 projects simultaneously)  
- Effort: Medium-High (processing layer is the hard part)
- Cost: Near-zero (CDX free, Gemini free, Ollama local)
- Related files: wayback-deep-archive-spec.md, vintage-agent.md,
                 ghost-book-division.md, ebay-identifier-spec.md
