# CREATIVE REVIEW TAXONOMY
## Master Reference for Creative Review Agent

> **Note:** This is a stub file. The full taxonomy was developed in a Claude.ai session.
> Paste the full content here when available, or rebuild from the description below.

---

## Purpose
Routes creative output to domain-appropriate reviewer panels based on content type and subgenre.
Weighted panels for blended content. Dissent protocol flags reviewer disagreements as data.

## Quality Gate Outputs
- **PUBLISH** — ready as-is
- **REVISE** — good core, needs polish
- **REWORK** — structural issues, significant rewrite needed
- **REJECT** — does not meet bar for this format/audience

---

## Genre Taxonomy

### Comedy (10 subgenres)
1. Observational / Stand-up adjacent
2. Absurdist / Surreal
3. Satirical / Political
4. Dark Comedy / Black Humor
5. Parody / Spoof
6. Romantic Comedy
7. Slapstick / Physical
8. Cringe Comedy
9. Dry / Deadpan
10. Character Comedy

**Reviewer Panel:** Domain comedian twin, comedy writer twin, audience proxy

---

### Drama
- Subgenres: Family, Legal, Medical, Political, Character Study
- **Reviewer Panel:** Drama writer twin, emotional authenticity reviewer, structure critic

### Horror
- Subgenres: Psychological, Supernatural, Slasher, Cosmic, Body Horror, Folk Horror
- **Reviewer Panel:** Horror author twin, fear mechanics reviewer, genre fan proxy

### Sci-Fi
- Subgenres: Hard SF, Space Opera, Cyberpunk, Dystopian, First Contact, Time Travel
- **Reviewer Panel:** Hard SF author twin, world-building critic, science accuracy reviewer

### Fantasy
- Subgenres: High Fantasy, Urban Fantasy, Dark Fantasy, Fairy Tale, Mythological
- **Reviewer Panel:** Fantasy author twin, mythology expert twin, internal logic reviewer

### Romance
- Subgenres: Contemporary, Historical, Paranormal, Romantic Suspense, Slow Burn
- **Reviewer Panel:** Romance author twin, emotional arc reviewer, reader proxy

### Thriller
- Subgenres: Psychological, Political, Tech, Crime, Spy, Legal
- **Reviewer Panel:** Thriller author twin, tension mechanics reviewer, plot logic critic

### Historical
- Subgenres: Period Drama, Alternative History, Historical Fiction, Biographical
- **Reviewer Panel:** Historical accuracy twin, period detail reviewer, anachronism detector

### Children / YA
- Subgenres: Picture Book, Middle Grade, Young Adult, Coming of Age
- **Reviewer Panel:** Child development expert twin, age-appropriate content reviewer, YA author twin

### Non-Fiction
- Subgenres: Memoir, Essay, Journalism, How-To, Biography
- **Reviewer Panel:** Fact-checker twin, narrative non-fiction author twin, clarity reviewer

### Marketing / Copywriting
- Subgenres: Product listing, Ad copy, Email, Landing page, Social
- **Reviewer Panel:** David Ogilvy twin, P.T. Barnum twin, conversion specialist twin

### Screenplay / Script
- Subgenres: Feature, Short, TV pilot, Web series, Shorts (Higgsfield format)
- **Reviewer Panel:** Script doctor twin, format specialist twin, director proxy

### Music
- Subgenres: Lyrics, Album concept, Liner notes
- **Reviewer Panel:** Music critic twin, lyric analysis reviewer, genre specialist twin

### Game
- Subgenres: Narrative design, Quest text, World-building, Tutorial
- **Reviewer Panel:** Game designer twin, player experience reviewer, narrative director twin

### Educational
- Subgenres: Curriculum, Tutorial, Reference, Explainer
- **Reviewer Panel:** Pedagogy expert twin, clarity reviewer, subject matter expert twin

---

## Blended Content Protocol

When content spans multiple genres, apply weighted panel:
- Identify primary genre (60% weight) and secondary genre (40% weight)
- Pull reviewers from both panels proportionally
- Flag blend in output: "Primary: [genre], Secondary: [genre]"

---

## Dissent Protocol

When reviewers disagree:
1. Log disagreement as data — do not suppress minority opinion
2. Flag to output: "Reviewer dissent: [character] rated REVISE vs council PUBLISH"
3. Escalate to Joe only if: majority is REJECT or dissent is on irreversible output

---

## Output Format

```
CREATIVE REVIEW RESULT
Genre: [primary] / [secondary if blended]
Panel: [characters consulted]
Verdict: PUBLISH | REVISE | REWORK | REJECT
Confidence: HIGH | MEDIUM | UNCERTAIN
Key feedback: [2-3 sentences]
Dissent: [if any]
```

---

*Full taxonomy pending: paste complete version from Claude.ai session when available.*
