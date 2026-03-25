# Wayback Machine Deep Archive Project
## Project Spec — captured 2026-03-26

---

## Core Insight
The pre-social-media internet (roughly 1996-2008) contains a fundamentally 
different quality of human communication than the current web:

- Written in paragraphs, not posts
- Domain-expert vocabulary used naturally among peers
- Long-form reasoning and elaboration
- Era-authentic word choice and cultural framing
- Unoptimized for SEO, engagement, or AI training
- Peer-to-peer knowledge transfer among genuine enthusiasts

This is a dataset gap that AI training has largely missed. Current LLMs are 
heavily weighted toward post-2010 internet. The pre-social web is an 
exploitable research and data advantage.

---

## The Research Question
How do different eras of internet communicate respond to the same topic?

- Word choice evolution across decades
- Depth and elaboration patterns (pre vs post social media)
- Domain vocabulary authenticity by era
- Expert vs novice communication patterns
- How truncation happened (bulletin board → forum → social → mobile)

This is diachronic corpus analysis applied to scraped archive data.

---

## Data Sources (Wayback Machine CDX API)
Already have CDX infrastructure from ghost-book and C2C AM work.

### Target Archive Categories

**Collector/Identification Forums (feeds eBay Identifier)**
- rec.antiques (Usenet 1993-2005)
- rec.collecting (Usenet)
- Early collector web forums (replacements.com community, etc.)
- Indiana Glass collector boards
- Vintage toy forums (pre-2005)
- Silver/hallmark identification boards

**Expert Knowledge Dumps (feeds Ghost Book + Vintage Agent)**
- Early hobbyist sites with deep how-to content
- Pre-Wikipedia reference pages maintained by genuine experts
- University extension service pages (agriculture, craft, trade)
- Trade association archives
- Technical manuals and spec sheets on early web

**Era Voice Capture (feeds CTW character system)**
- Early personal homepages (GeoCities archive)
- BBS/forum archives by decade (80s BBS → 90s web → early 2000s)
- Usenet groups by topic and year
- Mailing list archives (many on mail-archive.com)
- Early blog aggregators (BlogSpot 2001-2006)

**Game/Tech Archives (feeds Game Archaeology)**
- GameFAQs pre-2005 (walkthroughs written by players for players)
- Early gaming magazines (Electronic Gaming Monthly, GamePro digitized)
- Demo scene archives
- Abandonware discussion forums

**Coast to Coast AM / Fringe Research (feeds Conspiracy Tracker)**
- Already have C2C infrastructure
- Early paranormal/alternative research sites
- Pre-monetization UFO/conspiracy forums (genuine believers, not grifters)

---

## What To Extract

### For Each Archive Snapshot
- Timestamp (decade/year precision matters)
- Domain and community type
- Full text (not just preview)
- Thread structure if forum (who responds to whom)
- Vocabulary frequency analysis
- Sentence length and complexity metrics
- Domain-specific term usage

### Cross-Era Analysis
Same question/topic → different era responses:
- "How do I identify Indiana Glass?" (1999 forum vs 2024 Reddit)
- "What is the best way to store vinyl records?" (2001 AudiogoN vs 2023 r/vinyl)
- "How do I write a convincing character from the 1940s?" (2003 writing forum vs 2024 ChatGPT answer)

The delta between these is the dataset value.

---

## Applications

| Project | How Archive Data Helps |
|---------|----------------------|
| eBay Identifier | Collector vocabulary for accurate item identification |
| Vintage Agent | Era-authentic word choice, cultural context |
| CTW Characters | Authentic dialogue patterns by decade |
| Ghost Book | Pre-Wikipedia expert positions, minority views |
| Game Archaeology | Player-written game knowledge, era-accurate reviews |
| Conspiracy Tracker | Pre-monetization genuine belief patterns |
| AI Training Dataset | Potential commercial value — underrepresented era |

---

## The Commercial Angle
This dataset has value beyond personal projects:

- Fine-tuning dataset for era-specific AI voice models
- Historical language corpus for academic research
- Collector knowledge base (licensable to eBay, WorthPoint, etc.)
- Authentic vintage copywriting resource

If structured and cleaned properly, this archive could be a sellable dataset.

---

## Technical Approach
Already have:
- Wayback CDX infrastructure (from ghost-book and C2C work)
- scraper_utils.py and unicode_safe.py in utilities layer
- Gemini free tier for processing
- Ollama for local batch processing

Needs building:
- Forum thread reconstructor (replies → conversation trees)
- Era tagger (classify content by decade)
- Vocabulary extractor (domain-specific term frequency)
- Duplicate/noise filter (ads, navigation, boilerplate)
- Cross-era comparison engine

---

## Scheduler Integration
Add to overnight tasks:
- Weekly CDX discovery pass (new targets by category)
- Daily delta fetch on active target sites
- Gemini processing pass on raw fetched content
- Output to structured JSON per domain/era/category

---

## Project Status
- Status: WHITEBOARD — infrastructure partially exists
- Priority: HIGH (feeds 6 other projects)
- Effort: Medium (CDX already built, need processing layer)
- Cost: Near-zero (CDX free, Gemini free tier, Ollama local)
