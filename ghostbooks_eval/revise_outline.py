import json, os
from datetime import datetime

with open('ghost_outlines/linked_deep_outline.json', 'rb') as f:
    outline = json.loads(f.read().decode('utf-8-sig'))

# Current chapters
current_chapters = outline['chapters']

# NEW CHAPTER 1: Beyond Scale-Free
new_chapter_1 = {
    "chapter": 5,
    "title": "Beyond Scale-Free: Small Worlds, Robustness, and Limits",
    "description": "While scale-free networks dominate many domains, real networks often exhibit small-world properties, clustering, and robustness trade-offs that deviate from pure power law distributions. This chapter examines clustering coefficients, path lengths, attack tolerance, and the critical distinction between networks that appear scale-free and those that truly are.",
    "key_concepts": ["small-world networks", "clustering coefficients", "path length dynamics", "attack tolerance", "exponential cutoffs", "when power laws fail"]
}

# NEW CHAPTER 2: Network Failures
new_chapter_2 = {
    "chapter": 6,
    "title": "Network Failures and Transformations: Collapse, Phase Transitions, and Domain Limits",
    "description": "Networks don't just grow—they fragment, collapse, and undergo phase transitions. This chapter explores negative feedback mechanisms, self-regulation, cascade failures, and how domain-specific constraints create deviations from universal patterns.",
    "key_concepts": ["cascade failures", "phase transitions", "negative feedback", "domain-specific constraints", "infrastructure robustness", "network fragmentation"]
}

# Update chapter numbers for old chapters 5-6
updated_chapters = []
for ch in current_chapters:
    if ch['chapter'] >= 5:
        ch['chapter'] += 2
    updated_chapters.append(ch)

# Insert new chapters
updated_chapters.insert(4, new_chapter_1)
updated_chapters.insert(5, new_chapter_2)

# Revised thesis
revised_thesis = "Networks across all domains exhibit dominant organizing principles governed by power laws and preferential attachment, yet these universal patterns manifest with critical domain-specific variations, limitations, and counterexamples that reveal when and why networks defy the blueprint—providing a complete framework for understanding not just emergence, but robustness, failure, and adaptation."

# Update outline
outline['chapters'] = updated_chapters
outline['thesis'] = revised_thesis
outline['revision'] = {
    'date': datetime.now().isoformat(),
    'changes': [
        'Added Chapter 5: Beyond Scale-Free (addresses clustering, robustness, limits)',
        'Added Chapter 6: Network Failures (addresses collapse, phase transitions, domain deviations)',
        'Revised thesis to acknowledge limitations and domain-specific variations',
        'Now 8 chapters instead of 6'
    ],
    'peer_review_response': 'Addresses all reviewer feedback on universality overstatement'
}

# Save revised outline
with open('ghost_outlines/linked_deep_outline_REVISED.json', 'w', encoding='utf-8') as f:
    json.dump(outline, f, indent=2)

print('[REVISION COMPLETE]')
print(f'Total chapters: {len(updated_chapters)}')
print('New Structure (8 chapters):')
for ch in updated_chapters:
    print(f'  Ch {ch["chapter"]}: {ch["title"]}')
print(f'\nRevised Thesis: {revised_thesis[:100]}...')
