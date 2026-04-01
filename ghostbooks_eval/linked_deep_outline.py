import json, os, requests
from datetime import datetime

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, 'ghost_outlines')
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEY_FILE = os.path.join(BASE_DIR, 'anthropic_key.txt')
ANTHROPIC_API_KEY = ''
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        ANTHROPIC_API_KEY = f.read().decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-opus-4-20250514'

BOOK = {
    'title': 'Linked: the new science of networks',
    'domain': 'networks_emergence',
    'thesis': 'Networks across all domains follow universal organizing principles governed by power laws and preferential attachment, revealing how scale-free networks emerge and evolve through predictable patterns.'
}

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_claude(system, user):
    if not ANTHROPIC_API_KEY: return None
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': MODEL, 'max_tokens': 2000, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content: return content[0].get('text', '')
    except: pass
    return None

log_msg('=== LINKED: DEEP GHOSTWRITING OUTLINE ===')

# 1. Generate 6-chapter structure
log_msg('Generating 6-chapter structure...')
chapters_prompt = f'''Create a 6-chapter outline for a ghostwritten book based on this thesis:
"{BOOK["thesis"]}"

Return ONLY a JSON array with exactly 6 chapters. Each chapter should have:
- "chapter": number (1-6)
- "title": compelling chapter title
- "description": 2-3 sentence description of chapter focus
- "key_concepts": list of 3-4 key concepts covered

Format: [{{...}}, {{...}}, ...]
No preamble, only JSON.'''

chapters_response = call_claude('You are a book structure expert.', chapters_prompt)
chapters = []
if chapters_response:
    try:
        json_start = chapters_response.find('[')
        json_end = chapters_response.rfind(']') + 1
        chapters = json.loads(chapters_response[json_start:json_end])
        log_msg(f'✓ {len(chapters)} chapters created')
    except:
        log_msg('ERROR: Failed to parse chapters JSON')

# 2. Generate concept map (Mermaid)
log_msg('Generating concept map...')
concept_prompt = f'''Create a Mermaid flowchart (graph TD) showing how these concepts build toward the thesis:
Thesis: "{BOOK["thesis"]}"
Chapters: {[ch.get("title", "") for ch in chapters]}

Show 8-10 nodes with edges showing dependencies and causal flow.
Return ONLY the mermaid code, no explanation.'''

concept_map = call_claude('You are a knowledge architect.', concept_prompt) or '(concept map generation failed)'
log_msg('✓ Concept map created')

# 3. Generate expansion angles
log_msg('Generating expansion angles...')
expansion_prompt = f'''Given this thesis about networks:
"{BOOK["thesis"]}"

Identify 4-5 novel expansion angles or applications that could make this book original and valuable:
- How could this thesis apply to unexpected domains?
- What counterarguments or limitations should be acknowledged?
- What emerging research extends this thinking?
- How could this be used as a practical framework?

Format: numbered list with brief explanations.'''

expansion = call_claude('You are an innovation strategist.', expansion_prompt) or '(expansion angles generation failed)'
log_msg('✓ Expansion angles identified')

# 4. Generate content hooks (what to actually write)
log_msg('Generating content hooks...')
hooks_prompt = f'''For a ghostwritten book on network science based on this thesis:
"{BOOK["thesis"]}"

Generate 3-5 specific "content hooks" - concrete examples, stories, or frameworks that could anchor the book and make it memorable and practical.
These should be things readers can immediately apply or understand.

Format: bullet points with titles and 1-2 sentence descriptions.'''

hooks = call_claude('You are a content strategist.', hooks_prompt) or '(hooks generation failed)'
log_msg('✓ Content hooks generated')

# 5. Assemble full outline
outline = {
    'book': BOOK['title'],
    'domain': BOOK['domain'],
    'thesis': BOOK['thesis'],
    'chapters': chapters,
    'concept_map_mermaid': concept_map,
    'expansion_angles': expansion,
    'content_hooks': hooks,
    'generated_at': datetime.now().isoformat(),
    'status': 'READY_FOR_GHOSTWRITING'
}

# 6. Save
out_path = os.path.join(OUTPUT_DIR, 'linked_deep_outline.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(outline, f, indent=2)

log_msg(f'✓ Full outline saved: {out_path}')
log_msg(f'\nOUTLINE READY FOR GHOSTWRITING')
log_msg(f'Chapters: {len(chapters)}')
log_msg(f'Status: Ready to begin content synthesis')
