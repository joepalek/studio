#!/usr/bin/env python3
"""
AGENCY CHARACTER CREATOR
Takes a character spec and generates complete folder structure + all JSON/MD files.
Folder name format: {CharName}_{id_suffix} -- guarantees uniqueness across name collisions.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def create_character(spec):
    char_id = spec.get("id", "char-unknown")
    char_name = spec.get("name", "Unknown")
    universe = spec.get("universe", "original-fiction")
    status = spec.get("status", "draft")

    # Extract short suffix from ID for unique folder naming
    # e.g. "char-spec-claude-042" -> "c042", "char-spec-gemini-007" -> "g007", "char-spec-agent-015" -> "a015"
    id_parts = char_id.split("-")
    if len(id_parts) >= 4:
        source_initial = id_parts[2][0]  # c, g, or a
        num_part = id_parts[-1].zfill(3)
        id_suffix = source_initial + num_part
    else:
        id_suffix = char_id[-6:].replace("-", "")

    # Unique folder: "Casey Garcia_c002" -- human readable + collision-proof
    folder_name = char_name + "_" + id_suffix
    base_path = Path(f"G:/My Drive/Projects/_studio/agency/characters/{universe}/{folder_name}")
    base_path.mkdir(parents=True, exist_ok=True)

    for sub in ["images", "video", "audio", "scripts", "logs"]:
        (base_path / sub).mkdir(exist_ok=True)

    character_profile = {
        "id": char_id,
        "name": char_name,
        "universe": universe,
        "archetype": spec.get("archetype", ""),
        "created_date": datetime.now().isoformat(),
        "created_by": spec.get("created_by", "manual"),
        "status": status,
        "core_profile": {
            "name": char_name,
            "pronouns": spec.get("pronouns", "they/them"),
            "age": spec.get("age"),
            "personality_traits": spec.get("personality_traits", []),
            "voice": spec.get("voice", ""),
            "archetype_description": spec.get("archetype_description", ""),
            "backstory": spec.get("backstory", "")
        },
        "visual_specs": {
            "status": "draft",
            "locked_date": None,
            "locked_by": None,
            "description": spec.get("visual_description", ""),
            "references": spec.get("visual_references", []),
            "art_dept_notes": spec.get("art_dept_notes", ""),
            "approved_visual_assets": {}
        },
        "social_presence": {
            "accounts": [],
            "interaction_history": [],
            "marketing_plan": spec.get("marketing_plan", "")
        },
        "appearances": [],
        "media_assets": {"images": [], "video": [], "voice": []},
        "interaction_log": [],
        "metadata": {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "updated_by": "character-creator",
            "total_appearances": 0,
            "total_media_assets": 0,
            "total_interactions": 0,
            "revenue_potential": spec.get("revenue_potential", "MEDIUM"),
            "notes": spec.get("notes", "")
        }
    }

    # Slug uses name + id_suffix so filenames inside the folder are also unique
    slug = char_name.lower().replace(" ", "_").replace("'", "") + "_" + id_suffix

    profile_path = base_path / f"{slug}-profile.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(character_profile, f, indent=2)

    traits_md = "\n".join(f"- {t}" for t in spec.get("personality_traits", []))
    backstory_md = f"""# {char_name} ({char_id})

**Universe:** {universe}
**Archetype:** {spec.get("archetype", "")}
**Status:** {status}

## Core Profile

**Pronouns:** {spec.get("pronouns", "they/them")}
**Age:** {spec.get("age", "N/A")}
**Voice:** {spec.get("voice", "N/A")}

## Personality Traits

{traits_md}

## Backstory

{spec.get("backstory", "No backstory provided yet.")}

## Visual Direction

{spec.get("visual_description", "Art department will define visual identity.")}

### Art Notes

{spec.get("art_dept_notes", "Waiting for art department input.")}

## Social Media Plan

{spec.get("marketing_plan", "Marketing strategy to be defined.")}

---
*Character created: {datetime.now().isoformat()}*
"""
    with open(base_path / f"{slug}-backstory.md", "w", encoding="utf-8") as f:
        f.write(backstory_md)

    with open(base_path / "logs" / f"{slug}-media-log.json", "w", encoding="utf-8") as f:
        json.dump({
            "character_id": char_id, "character_name": char_name,
            "created": datetime.now().isoformat(),
            "total_images": 0, "total_videos": 0, "total_audio": 0,
            "images": [], "videos": [], "audio": [],
            "notes": "Log populated as character appears in projects and media is created"
        }, f, indent=2)

    with open(base_path / "logs" / f"{slug}-interaction-log.json", "w", encoding="utf-8") as f:
        json.dump({
            "character_id": char_id, "character_name": char_name,
            "platforms": [], "total_interactions": 0,
            "total_coins_earned": 0, "total_coins_spent": 0,
            "interactions": [],
            "notes": "Log populated as character interacts on social media"
        }, f, indent=2)

    with open(base_path / "logs" / f"{slug}-appearances.json", "w", encoding="utf-8") as f:
        json.dump({
            "character_id": char_id, "character_name": char_name,
            "total_projects": 0, "appearances": [],
            "notes": "Log populated as character is assigned to projects"
        }, f, indent=2)

    locked = "Yes" if character_profile["visual_specs"]["locked_date"] else "No"
    readme = f"""# {char_name}

**ID:** {char_id}
**Universe:** {universe}
**Archetype:** {spec.get("archetype", "")}
**Status:** {status}
**Created:** {datetime.now().isoformat()}

## Quick Reference

- **Profile:** {slug}-profile.json
- **Backstory:** {slug}-backstory.md
- **Media Log:** logs/{slug}-media-log.json
- **Interaction Log:** logs/{slug}-interaction-log.json
- **Appearances:** logs/{slug}-appearances.json

## Folders

- **images/** -- All character images (portraits, action shots, etc.)
- **video/** -- All video clips featuring character
- **audio/** -- Voice recordings, dialogue, song clips
- **scripts/** -- Scripts for projects this character appears in
- **logs/** -- All tracking logs (media, interactions, appearances)

## Status

- Visual specs: {character_profile["visual_specs"]["status"]}
- Locked visual: {locked}

---

*Managed by: Agency Character Creator*
"""
    with open(base_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"Character created: {char_name} ({id_suffix})")
    print(f"  ID: {char_id}")
    print(f"  Folder: {folder_name}")
    print(f"  Universe: {universe}")
    print(f"  Path: {base_path}")

    return {
        "success": True,
        "character_id": char_id,
        "character_name": char_name,
        "folder_name": folder_name,
        "path": str(base_path),
        "profile_file": str(profile_path)
    }


if __name__ == "__main__":
    sample_spec = {
        "id": "char-spec-claude-042",
        "name": "Sam Rodriguez",
        "universe": "inmates-vs-guards",
        "archetype": "prison_chaplain",
        "created_by": "test",
        "status": "draft",
        "pronouns": "she/her",
        "age": 22,
        "personality_traits": ["practical", "charismatic", "artistic", "analytical"],
        "voice": "Playful and irreverent.",
        "backstory": "Made a pivotal decision that changed the course of their life.",
        "revenue_potential": "MEDIUM"
    }
    result = create_character(sample_spec)
    print("\nResult: " + str(result))
