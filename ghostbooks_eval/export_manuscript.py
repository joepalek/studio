import json, os
from datetime import datetime

# Extract Ch 1 & 2 full text for DOCX export

with open('ghost_outlines/ch1_FULL_PROSE.json', 'rb') as f:
    ch1 = json.loads(f.read().decode('utf-8-sig'))

with open('ghost_outlines/ch2_FULL_PROSE.json', 'rb') as f:
    ch2 = json.loads(f.read().decode('utf-8-sig'))

def extract_full_text(ch):
    parts = []
    if ch.get('introduction'):
        parts.append(ch['introduction'])
    for sec in ch.get('sections', []):
        if sec.get('content'):
            parts.append(f"\n{sec['title']}\n" + "="*len(sec['title']) + f"\n{sec['content']}")
    if ch.get('conclusion'):
        parts.append(f"\nConclusion\n" + "="*10 + f"\n{ch['conclusion']}")
    return '\n\n'.join(parts)

ch1_text = extract_full_text(ch1)
ch2_text = extract_full_text(ch2)

# Save as plain text for conversion to DOCX
with open('../linked_ch1_ch2_manuscript.txt', 'w', encoding='utf-8') as f:
    f.write("LINKED: THE NEW SCIENCE OF NETWORKS\n")
    f.write("="*50 + "\n\n")
    f.write("CHAPTER 1: The Hidden Architecture of Everything\n")
    f.write("-"*50 + "\n\n")
    f.write(ch1_text)
    f.write("\n\n" + "="*50 + "\n\n")
    f.write("CHAPTER 2: The Power Law Revolution\n")
    f.write("-"*50 + "\n\n")
    f.write(ch2_text)

print('[MANUSCRIPT EXTRACTED]')
print('File: linked_ch1_ch2_manuscript.txt')
print(f'Ch 1: {len(ch1_text)} chars')
print(f'Ch 2: {len(ch2_text)} chars')
print(f'Total: {len(ch1_text) + len(ch2_text)} chars (~{(len(ch1_text) + len(ch2_text)) // 5} words)')
