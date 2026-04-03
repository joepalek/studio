#!/usr/bin/env python3
"""
CHARACTER SPEC GENERATOR
Produces 300 random personality specs daily (100 from Claude, 100 from Gemini, 100 from Agent).
Generates diverse characters across: original fiction, inmates-vs-guards, band-members, other.
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path

# Universe distribution
UNIVERSE_DIST = {
    "original_fiction": 0.40,
    "inmates_vs_guards": 0.30,
    "band_members": 0.20,
    "other": 0.10
}

# Personality trait pools
PERSONALITY_TRAITS = {
    "positive": [
        "empathetic", "resilient", "creative", "thoughtful", "loyal", 
        "courageous", "principled", "charismatic", "intelligent", "observant",
        "patient", "compassionate", "determined", "adaptable", "insightful"
    ],
    "neutral": [
        "analytical", "practical", "reserved", "energetic", "cautious",
        "ambitious", "independent", "collaborative", "meticulous", "spontaneous",
        "intuitive", "logical", "artistic", "technical", "diplomatic"
    ],
    "conflicted": [
        "rebellious", "haunted", "cynical", "obsessive", "paranoid",
        "reckless", "possessive", "insecure", "vindictive", "delusional",
        "conflicted", "jaded", "suspicious", "impulsive", "destructive"
    ]
}

ARCHETYPES = {
    "original_fiction": [
        "unlikely_hero", "anti_hero", "mentor", "trickster", "sage",
        "lover", "everyman", "innocent", "explorer", "caregiver"
    ],
    "inmates_vs_guards": [
        "reformed_inmate", "hardened_criminal", "idealistic_guard", 
        "corrupt_guard", "prison_chaplain", "lifer", "young_offender",
        "prison_mentor", "informant", "political_prisoner"
    ],
    "band_members": [
        "lead_vocalist", "guitarist", "bassist", "drummer", "keyboardist",
        "frontman", "musical_genius", "troubled_artist", "session_musician",
        "band_leader"
    ],
    "other": [
        "entrepreneur", "activist", "scholar", "mystic", "artist",
        "athlete", "detective", "doctor", "teacher", "wanderer"
    ]
}

VOICE_STYLES = [
    "quiet and introspective",
    "loud and confident",
    "poetic and philosophical",
    "direct and blunt",
    "sarcastic and witty",
    "warm and empathetic",
    "cold and analytical",
    "playful and irreverent",
    "measured and careful",
    "passionate and intense"
]

VISUAL_HINTS = [
    "rough around the edges",
    "polished and refined",
    "weathered but strong",
    "youthful and energetic",
    "mysterious and dark",
    "bright and approachable",
    "imposing physical presence",
    "deceptively unassuming",
    "artistic in appearance",
    "military bearing"
]


def generate_random_spec(source_agent, spec_number):
    """Generate a single random character spec"""
    
    # Pick universe based on distribution
    universe = random.choices(
        list(UNIVERSE_DIST.keys()),
        weights=list(UNIVERSE_DIST.values())
    )[0]
    
    # Pick archetype for universe
    archetype = random.choice(ARCHETYPES[universe])
    
    # Pick personality traits
    trait_count = random.randint(4, 7)
    traits = []
    for _ in range(trait_count):
        category = random.choice(list(PERSONALITY_TRAITS.keys()))
        traits.append(random.choice(PERSONALITY_TRAITS[category]))
    traits = list(set(traits))  # Remove duplicates
    
    # Generate character name (simple approach, can be enhanced)
    first_names = ["Marcus", "Jade", "Alex", "Morgan", "River", "Sam", "Casey", "Jordan", 
                   "Alex", "Morgan", "Phoenix", "Dakota", "Blake", "Riley", "Skyler"]
    last_names = ["Chen", "Torres", "O'Brien", "Smith", "Johnson", "Williams", "Miller",
                  "Davis", "Rodriguez", "Martinez", "Brown", "Garcia", "Anderson"]
    
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    # Generate backstory snippets
    backstory_templates = [
        "Grew up in a small town before moving to the city looking for opportunity.",
        "Has a complicated relationship with their past that shapes everything they do.",
        "Discovered a hidden talent late in life and has been pursuing it obsessively.",
        "Carries deep regrets about choices made years ago.",
        "Rose from difficult circumstances through sheer determination.",
        "Comes from privilege but rejects it to find authentic meaning.",
        "Has been searching for something they can't quite name.",
        "Made a pivotal decision that changed the course of their life.",
        "Struggles with the gap between who they are and who they want to be.",
        "Found solace in an unexpected place and built their life around it."
    ]
    backstory = random.choice(backstory_templates)
    
    # Assemble spec — ID includes datestamp so each daily batch has unique IDs
    date_tag = datetime.now().strftime("%Y%m%d")
    spec = {
        "id": f"char-spec-{source_agent}-{date_tag}-{spec_number:03d}",
        "name": name,
        "universe": universe,
        "archetype": archetype,
        "source": source_agent,
        "created_date": datetime.now().isoformat(),
        "personality_traits": traits,
        "voice": random.choice(VOICE_STYLES),
        "visual_hint": random.choice(VISUAL_HINTS),
        "backstory": backstory,
        "age": random.choice([18, 22, 28, 35, 42, 55, 65]),
        "pronouns": random.choice(["he/him", "she/her", "they/them"]),
        "status": "ungraded"
    }
    
    return spec


def generate_daily_batch(claude_count=100, gemini_count=100, agent_count=100):
    """Generate daily batch of 300 specs (100 from each source)"""
    
    all_specs = []
    
    print(f"Generating character specs batch...")
    print(f"  Claude: {claude_count} specs")
    
    for i in range(claude_count):
        spec = generate_random_spec("claude", i+1)
        all_specs.append(spec)
    
    print(f"  Gemini: {gemini_count} specs")
    
    for i in range(gemini_count):
        spec = generate_random_spec("gemini", i+1)
        all_specs.append(spec)
    
    print(f"  Agent: {agent_count} specs")
    
    for i in range(agent_count):
        spec = generate_random_spec("agent", i+1)
        all_specs.append(spec)
    
    # Save batch
    base_path = Path("G:/My Drive/Projects/_studio/agency/spec-queue")
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Daily file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_file = base_path / f"spec-batch-{timestamp}.json"
    
    batch_data = {
        "generated": datetime.now().isoformat(),
        "batch_date": datetime.now().strftime("%Y-%m-%d"),
        "total_specs": len(all_specs),
        "by_source": {
            "claude": claude_count,
            "gemini": gemini_count,
            "agent": agent_count
        },
        "by_universe": {},
        "specs": all_specs
    }
    
    # Count by universe
    for spec in all_specs:
        universe = spec["universe"]
        batch_data["by_universe"][universe] = batch_data["by_universe"].get(universe, 0) + 1
    
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2)
    
    # Also save to current queue (so grading interface always reads the latest)
    queue_file = base_path / "spec-queue-current.json"
    with open(queue_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"Batch generated: {len(all_specs)} total specs")
    print(f"By universe:")
    for universe, count in sorted(batch_data["by_universe"].items()):
        pct = (count / len(all_specs)) * 100
        print(f"  {universe}: {count} ({pct:.0f}%)")
    print(f"\nSaved to: {batch_file}")
    print(f"Queue file: {queue_file}")
    print(f"{'='*70}\n")
    
    return batch_data


if __name__ == "__main__":
    batch = generate_daily_batch(100, 100, 100)
    
    # Show sample specs
    print(f"Sample specs (first 3):\n")
    for spec in batch["specs"][:3]:
        print(f"  {spec['name']} ({spec['universe']})")
        print(f"    Archetype: {spec['archetype']}")
        print(f"    Traits: {', '.join(spec['personality_traits'][:3])}")
        print(f"    Voice: {spec['voice']}")
        print()
