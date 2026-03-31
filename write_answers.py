import json
from datetime import datetime

NOW = datetime.now().isoformat()[:19]
TODAY = datetime.now().strftime("%Y-%m-%d")

inbox_path = "G:/My Drive/Projects/_studio/mobile-inbox.json"
inbox = json.load(open(inbox_path, encoding='utf-8', errors='replace'))
if isinstance(inbox, dict):
    inbox = inbox.get('items', [])

# Remove the combined placeholder — these are two distinct projects
inbox = [i for i in inbox if i.get('id') != f"project-ebay-image-listing-app-{TODAY}"]

new_items = [
    {
        "id": f"project-ebay-image-listing-app-{TODAY}",
        "project": "_studio",
        "type": "new_project_idea",
        "title": "eBay Image Listing App (Photo → Draft Listing)",
        "question": "Ready to scaffold the eBay Image Listing App?",
        "context": (
            "Scoped Mar 13 2026 (chat: 5be8454e-aa34-4f60-8750-f4083a222b0c). "
            "Upload photo → Gemini Vision identifies all items → eBay sold price lookup → "
            "generates listing title + suggested price. Lot logic for items under $15. "
            "Exports to eBay as draft listings via Trading API. "
            "CREATION tool — distinct from Listing Optimizer (bulk CSV optimizer of existing listings). "
            "Blocked on eBay Developer Program OAuth setup. "
            "eBay API infrastructure shared with Listing Optimizer + Arbitrage Pulse."
        ),
        "status": "pending",
        "created": TODAY,
        "tags": ["ebay", "new-project", "vision-api", "listing-creator", "gemini"],
        "prior_chat": "https://claude.ai/chat/5be8454e-aa34-4f60-8750-f4083a222b0c"
    },
    {
        "id": f"project-ebay-consensus-engine-{TODAY}",
        "project": "_studio",
        "type": "new_project_idea",
        "title": "eBay Item Identifier — Consensus Engine (Visual Lookup)",
        "question": "Ready to formalize the Consensus Engine as a studio project?",
        "context": (
            "Fully specced Mar 27 2026 (chat: f57a73f0-8f37-4d9e-93e3-bcf80f92bcf7). "
            "Gemini-generated architecture reviewed and approved. "
            "Replaces Google Lens → manual eBay search workflow for resellers. "
            "6-track consensus engine: "
            "(1) Pixel Matcher — Google/eBay Visual Search API baseline. "
            "(2) Attribute Analyst — VLM structured JSON {maker, pattern, material, era}. "
            "(3) Hallmark/Maker Mark OCR — PaddleOCR-VL, overrides on Lion Passant etc. "
            "(4) Archive Historian RAG — Internet Archive trade catalogs, official color names. "
            "(5) Molded Mark OCR — copyright dates, manufacturer codes, era-locks results. "
            "(6) Instruction Manual cross-ref — identifies parts from incomplete sets. "
            "KEY FEATURE: Reroll — after results come back, pick best matches, "
            "re-run search using top results as new anchors to refine further. "
            "Multi-image input: hero shot + bottom mark + molded date + scale photo, "
            "each analyzed by appropriate track. "
            "Also on whiteboard scored 8/10 as eBay Consensus Engine. "
            "IDENTIFICATION tool — complements Image Listing App (creation) and "
            "Listing Optimizer (bulk optimization)."
        ),
        "status": "pending",
        "created": TODAY,
        "tags": ["ebay", "new-project", "consensus-engine", "visual-lookup", "reroll",
                 "collectibles", "VLM", "OCR", "RAG"],
        "prior_chat": "https://claude.ai/chat/f57a73f0-8f37-4d9e-93e3-bcf80f92bcf7"
    }
]

existing_ids = {i.get('id') for i in inbox}
for item in new_items:
    if item['id'] not in existing_ids:
        inbox.append(item)
        print(f"  added: {item['title']}")

json.dump(inbox, open(inbox_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print("mobile-inbox.json updated")
