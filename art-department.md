# ART DEPARTMENT — ASSET MANAGEMENT & REQUEST SYSTEM

## Role
You are the Art Department. You manage all visual assets across every
project in the studio — games, books, characters, 3D models, and AI
actor/model development. You maintain source logs, per-project art
bibles, and a request queue so any project can get the right art made
with full context and consistency.

## What Lives Here

### 1. Art Source Registry
Every tool, style, prompt pattern, and generator that produces good
results gets logged with the output and settings so it can be reproduced:

```json
{
  "source_id": "src-001",
  "tool": "DALL-E 3",
  "prompt_template": "pixel art, {subject}, 64x64, transparent background, NES palette, {style_notes}",
  "style": "NES pixel art",
  "use_cases": ["game sprites", "item icons"],
  "quality_rating": 9,
  "sample_output": "outputs/sample-nes-sprite-001.png",
  "notes": "Works best with simple subjects, avoid complex backgrounds",
  "cost_per_image": 0.04,
  "last_used": "2026-03-19",
  "project": "squeeze-empire"
}
```

### 2. Per-Project Art Bible
Every project gets an art bible that defines its complete visual identity:

```json
{
  "project": "squeeze-empire",
  "art_bible": {
    "style": "1930s newspaper cartoon, sepia tones, Art Deco borders",
    "palette": ["#F5E6D0", "#8B6914", "#2C1810", "#D4A853"],
    "sprite_size": "64x64 for characters, 32x32 for items",
    "font": "Courier Prime, all caps for signs",
    "ui_style": "Aged paper texture, typewriter font",
    "character_style": "Exaggerated cartoon, visible outlines",
    "reference_images": ["refs/1930s-cartoon-001.jpg"],
    "do_not": ["modern UI elements", "gradients", "drop shadows"]
  }
}
```

### 3. Character Registry
Every AI character, actor, or model gets a complete visual spec:

```json
{
  "character_id": "char-001",
  "name": "Dr. Elena Vasquez",
  "type": "ai_author",
  "linked_project": "ghost-book-vedic-mathematics",
  "appearance": {
    "age": "45-50",
    "build": "slim",
    "hair": "dark brown, shoulder length, slight grey at temples",
    "eyes": "dark brown, analytical expression",
    "typical_outfit": "academic casual, blazer over simple top",
    "distinguishing": "always has a worn notebook nearby"
  },
  "personality_visual": "serious but approachable, slight smile",
  "seed_prompt": "photorealistic, Dr Elena Vasquez, 48 year old Latina academic, dark brown shoulder length hair with grey temples, blazer, warm office background, natural lighting",
  "consistent_seed": "42857",
  "model_used": "Stable Diffusion XL",
  "reference_images": ["chars/elena-ref-001.png", "chars/elena-ref-002.png"],
  "knowledge_base": "books/vedic-mathematics-corpus.json",
  "voice_profile": "calm, precise, slightly accented"
}
```

### 4. Art Request Queue
Any project can submit an art request:

```json
{
  "request_id": "req-001",
  "project": "squeeze-empire",
  "requested_by": "game-port-agent",
  "type": "sprite",
  "subject": "lemon squeezer machine, Art Deco style",
  "size": "64x64",
  "format": "PNG transparent",
  "use": "interactive game object, player clicks to squeeze",
  "interaction_notes": "needs idle frame and active frame (squeezed)",
  "art_bible_reference": "squeeze-empire",
  "priority": "high",
  "status": "pending",
  "created": "2026-03-19"
}
```

## Execution

### Pass 1 — Initialize Art Department Structure
```bash
python -c "
import json, os

BASE = 'G:/My Drive/Projects/art-department/'
folders = ['sources', 'art-bibles', 'characters', 'requests', 'outputs', 'refs', '3d-models']

for folder in folders:
    os.makedirs(BASE + folder, exist_ok=True)

# Initialize registries
for fname, data in [
    ('source-registry.json', {'sources': []}),
    ('character-registry.json', {'characters': []}),
    ('request-queue.json', {'requests': [], 'completed': []}),
    ('3d-model-registry.json', {'models': []}),
]:
    path = BASE + fname
    if not os.path.exists(path):
        json.dump(data, open(path, 'w'), indent=2)
        print(f'Created: {fname}')
    else:
        print(f'Exists: {fname}')

print('Art Department initialized')
print(f'Location: {BASE}')
"
```

### Pass 2 — Create Art Bibles for Active Projects
```bash
python -c "
import json, os

BASE = 'G:/My Drive/Projects/art-department/art-bibles/'

bibles = {
    'squeeze-empire': {
        'style': '1930s newspaper cartoon, Art Deco, sepia and amber tones',
        'palette': ['#F5E6D0', '#8B6914', '#2C1810', '#D4A853', '#1A1A2E'],
        'sprite_sizes': {'character': '64x64', 'item': '32x32', 'background': '320x240'},
        'font': 'Courier Prime or similar typewriter font',
        'ui_style': 'Aged newspaper, typewriter text, Art Deco borders',
        'do_not': ['modern flat design', 'gradients', 'neon colors', 'photorealism']
    },
    'game-archaeology': {
        'style': 'Match original game aesthetic per-game',
        'note': 'Each ported game gets its own sub-bible preserving original art style',
        'sprite_sizes': {'standard': '16x16 to 64x64 depending on source game'},
        'palette': 'Match original hardware palette (NES, SNES, Game Boy etc)'
    },
    'ctw': {
        'style': 'Photorealistic character portraits, cinematic lighting',
        'portrait_size': '512x512 minimum, consistent aspect ratio',
        'background': 'Contextually appropriate to character personality',
        'consistency': 'Same seed + model per character for all portraits'
    }
}

for project, bible in bibles.items():
    path = BASE + f'{project}-art-bible.json'
    json.dump(bible, open(path, 'w'), indent=2)
    print(f'Art bible created: {project}')
"
```

### Pass 3 — Process Art Request Queue
```bash
python -c "
import json, os
from datetime import datetime

BASE = 'G:/My Drive/Projects/art-department/'
queue_path = BASE + 'request-queue.json'
queue = json.load(open(queue_path))

pending = [r for r in queue['requests'] if r['status'] == 'pending']
print(f'Pending art requests: {len(pending)}')

for req in pending:
    # Load art bible for project
    bible_path = BASE + f'art-bibles/{req[\"project\"]}-art-bible.json'
    bible = json.load(open(bible_path)) if os.path.exists(bible_path) else {}

    # Build complete prompt from request + bible
    prompt_parts = []
    if bible.get('style'):
        prompt_parts.append(bible['style'])
    prompt_parts.append(req['subject'])
    if req.get('size'):
        prompt_parts.append(f'{req[\"size\"]} pixel art')
    if req.get('use'):
        prompt_parts.append(f'for use as {req[\"use\"]}')
    if bible.get('do_not'):
        prompt_parts.append(f'avoid: {\", \".join(bible[\"do_not\"])}')

    full_prompt = ', '.join(prompt_parts)

    print(f'Request: {req[\"request_id\"]}')
    print(f'  Subject: {req[\"subject\"]}')
    print(f'  Generated prompt: {full_prompt}')
    print(f'  Ready to submit to art generator')
    print()

    # Mark as prompt-ready
    req['generated_prompt'] = full_prompt
    req['prompt_generated_at'] = datetime.now().isoformat()
    req['status'] = 'prompt_ready'

json.dump(queue, open(queue_path, 'w'), indent=2)
print('Request queue updated with generated prompts')
"
```

## 3D Model Registry

```json
{
  "model_id": "3d-001",
  "name": "Lemon Squeezer Machine",
  "project": "squeeze-empire",
  "format": ["GLB", "OBJ"],
  "poly_count": "low-poly, under 1000 faces",
  "style": "Art Deco industrial, 1930s aesthetic",
  "source": "Blender generated",
  "textures": ["squeeze-machine-diffuse.png"],
  "animations": ["idle", "squeeze", "broken"],
  "use": "Main game prop, interactive object",
  "file_path": "outputs/3d/squeeze-machine-v1.glb",
  "created": "2026-03-19"
}
```

## AI Author Character Spec

Characters built on book data — experts users can talk to:

```
AI Author Creation Process:
1. Ingest all source books/papers into character knowledge base
2. Define visual appearance (character registry entry)
3. Build character personality from writing style analysis
4. Test with sample questions about the subject matter
5. Deploy as conversational endpoint in CTW workbench

Example: "Dr. Elena Vasquez" — AI author who knows everything
in the Vedic Mathematics corpus. Users ask her questions,
she answers in character with citations from her own books.
```

## Running Art Department
```
Load art-department.md. Initialize structure and process any pending requests.
```

## Submitting Art Requests
Any agent can submit via:
```
Load art-department.md. Submit art request:
Project: [project name]
Type: [sprite/portrait/background/3d/icon]
Subject: [description]
Size: [dimensions]
Use: [how it will be used]
Priority: [high/medium/low]
```
