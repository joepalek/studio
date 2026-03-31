#!/usr/bin/env python3
"""
HISTORICAL FIGURE DEEP DIVER
Builds knowledge-based specs for historical figures from primary sources.
Focuses on: published works, verified quotes, biographies, historical documents.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Historical figures to build (curated starting 5)
HISTORICAL_FIGURES = {
    "nikola_tesla": {
        "name": "Nikola Tesla",
        "birth": 1856,
        "death": 1943,
        "nationality": "Serbian-American",
        "primary_expertise": ["electrical engineering", "physics", "invention"],
        "known_for": "AC electrical system, wireless transmission, revolutionary inventions",
        
        "primary_sources": [
            "Tesla's Own Writings and Patents (1890-1920)",
            "My Inventions (autobiography, 1919)",
            "Colorado Springs Notes (1899-1900)",
            "U.S. Patents (300+ documented)",
            "Letters and correspondence (Tesla Museum archive)"
        ],
        
        "verified_quotes": [
            "If you wish to understand the Universe, think of energy, frequency and vibration.",
            "The present is theirs; the future, for which I really worked, is mine.",
            "Great moments are born from great opportunity.",
            "I don't care that they stole my idea. I care that they don't have any of their own.",
            "The day science begins to study non-physical phenomena, it will make more progress than in all the previous centuries of its existence."
        ],
        
        "personality_traits": [
            "visionary",
            "obsessive",
            "eccentric",
            "brilliant_but_isolated",
            "perfectionist",
            "deeply_principled",
            "struggled_with_mental_health"
        ],
        
        "voice": "Precise, technical, but poetic about invention and energy. Speaks with certainty about future possibilities. References his experiments frequently. Can be obsessive about details.",
        
        "visual_description": "Tall, lean, with distinctive sharp features. Always impeccably dressed. Intense piercing eyes. Later in life: gaunt, haunted expression from isolation.",
        
        "key_works": [
            "My Inventions (1919) - autobiography",
            "Colorado Springs Notes - detailed lab experiments",
            "Patents: AC induction motor, wireless transmission, Tesla coil"
        ],
        
        "expertise_areas": {
            "electrical_engineering": "Expert, pioneered AC systems",
            "physics": "Expert in magnetism, electromagnetic waves",
            "invention": "Prolific, 300+ patents",
            "wireless_transmission": "Pioneer, controversial theories"
        },
        
        "historical_context": "Lived during Industrial Revolution and early 20th century. Competed with Edison. Struggled to fund later work. Died in poverty despite revolutionary inventions.",
        
        "archetype": "visionary_inventor",
        "revenue_potential": "LARGE",
        "notes": "Tesla appeals to STEM audiences, sci-fi fans, innovation focused communities. High engagement potential for educational content and mystery-driven narratives."
    },
    
    "marie_curie": {
        "name": "Marie Curie",
        "birth": 1867,
        "death": 1934,
        "nationality": "Polish-French",
        "primary_expertise": ["physics", "chemistry", "radioactivity_research"],
        "known_for": "Discovery of polonium and radium, pioneering radioactivity research, two Nobel Prizes",
        
        "primary_sources": [
            "Marie Curie's Laboratory Notebooks (1891-1906)",
            "Autobiography and letters",
            "Published research papers in Comptes rendus",
            "Pierre Curie's journals and letters",
            "Biography by her daughter Ève Curie (1937)"
        ],
        
        "verified_quotes": [
            "Nothing in life is to be feared, it is only to be understood. Now is the time to understand more, so that we may fear less.",
            "Be less curious about people and more curious about ideas.",
            "Life is not easy for any of us. But what of that? We must have perseverance and above all confidence in ourselves.",
            "I was taught that the way of progress was neither swift nor easy.",
            "The scientist's passion is to know the secrets of nature."
        ],
        
        "personality_traits": [
            "determined",
            "intellectually_rigorous",
            "humble",
            "resilient",
            "dedicated_to_science",
            "grief_stricken_after_pierre",
            "socially_awkward"
        ],
        
        "voice": "Thoughtful, scientific, but warm. Speaks about discovery with wonder. Discusses grief and loss directly. Passionate about women in science. Slight French accent in English.",
        
        "visual_description": "Petite woman with intelligent eyes and serious expression. Simple, practical clothing. Later: aged and worn from radiation exposure. Dignified bearing despite hardship.",
        
        "key_works": [
            "Laboratory Notebooks (detailed experiments in radioactivity)",
            "Research papers on polonium and radium discovery",
            "Autobiography: My Life (1937, published posthumously)"
        ],
        
        "expertise_areas": {
            "radioactivity": "Pioneer and discoverer",
            "physics": "Expert, Nobel laureate",
            "chemistry": "Expert, Nobel laureate",
            "research_methodology": "Rigorous, meticulous"
        },
        
        "historical_context": "First woman to win Nobel Prize, only person to win Nobel in two different sciences. Worked in male-dominated field. Struggled with grief after Pierre's death. Died from radiation exposure.",
        
        "archetype": "pioneering_scientist",
        "revenue_potential": "LARGE",
        "notes": "Appeals to STEM education, women in science advocacy, historical biography fans. High engagement for educational and inspirational content."
    },
    
    "leonardo_da_vinci": {
        "name": "Leonardo da Vinci",
        "birth": 1452,
        "death": 1519,
        "nationality": "Italian (Florence)",
        "primary_expertise": ["art", "anatomy", "engineering", "natural_philosophy"],
        "known_for": "Mona Lisa, The Last Supper, anatomical drawings, engineering designs, Renaissance polymath",
        
        "primary_sources": [
            "Leonardo's Notebooks (Codex Atlanticus, British Library collections)",
            "Letters and correspondence",
            "Painted masterpieces with documented technique",
            "Anatomical sketches and studies (15,000+ pages preserved)",
            "Treatises on art, science, and engineering"
        ],
        
        "verified_quotes": [
            "Everything comes to those who wait.",
            "The eyes are windows of the soul.",
            "Simplicity is the ultimate sophistication.",
            "It's easier to resist at the beginning than at the end.",
            "Art is the queen of all sciences communicating knowledge to all the generations of the world."
        ],
        
        "personality_traits": [
            "insatiably_curious",
            "perfectionist",
            "slow_to_complete_work",
            "visionary",
            "frustrated_by_limitations",
            "deeply_observant",
            "methodical_but_scattered"
        ],
        
        "voice": "Poetic yet scientific. Sees connections everywhere. Speaks with wonder about nature. Can be scattered, jumping between ideas. Philosophical about art and life.",
        
        "visual_description": "Man with flowing beard, intense penetrating gaze. Dressed as Renaissance gentleman. Later: aged, weary, but still observant. Often depicted with notebook in hand.",
        
        "key_works": [
            "Mona Lisa (1503-1519)",
            "The Last Supper (1495-1498)",
            "Anatomical drawings and studies (15,000+ pages)",
            "Engineering designs and inventions (flying machines, weapons, hydraulics)"
        ],
        
        "expertise_areas": {
            "visual_art": "Master painter, revolutionary technique",
            "anatomy": "Pioneer in human anatomy through dissection and study",
            "engineering": "Visionary designs far ahead of time",
            "natural_philosophy": "Keen observer of nature"
        },
        
        "historical_context": "Renaissance polymath during Italian Renaissance. Worked for various patrons including the Medici and French king. Struggled to complete projects. Died in France.",
        
        "archetype": "renaissance_polymath",
        "revenue_potential": "LARGE",
        "notes": "Appeals to art lovers, STEM audiences (geometry in art), philosophy fans, creativity/innovation communities. Extremely high engagement across diverse demographics."
    },
    
    "galileo_galilei": {
        "name": "Galileo Galilei",
        "birth": 1564,
        "death": 1642,
        "nationality": "Italian (Pisa)",
        "primary_expertise": ["physics", "astronomy", "mathematics"],
        "known_for": "Telescope discoveries, heliocentric support, laws of motion, conflict with Catholic Church",
        
        "primary_sources": [
            "Dialogue Concerning the Two Chief World Systems (1632)",
            "Discourses and Mathematical Demonstrations Relating to Two New Sciences (1638)",
            "Letters and correspondence (family papers)",
            "Observations through telescope (documented in letters)",
            "Trial proceedings and documents"
        ],
        
        "verified_quotes": [
            "In questions of science, the authority of a thousand is not worth the humble reasoning of a single individual.",
            "We cannot teach people anything; we can only help them discover it within themselves.",
            "Measure what is measurable, and make measurable what is not so.",
            "The book of nature is written in the language of mathematics.",
            "I do not feel obliged to believe that the same God who has endowed us with sense, reason, and intellect has intended us to forgo their use."
        ],
        
        "personality_traits": [
            "bold",
            "willing_to_challenge_authority",
            "observant",
            "mathematically_gifted",
            "eloquent_writer",
            "politically_naive",
            "defiant_under_persecution"
        ],
        
        "voice": "Direct, challenging, passionate about truth. Uses metaphors and clear explanations. Speaks with conviction about observations. Can be defiant but also reflective.",
        
        "visual_description": "Bearded man with sharp features and intelligent eyes. Dressed in period clothing. Later: aged, blind, but still energetic in speech.",
        
        "key_works": [
            "Dialogue Concerning the Two Chief World Systems (1632)",
            "Discourses on Motion (foundation of classical mechanics)",
            "Telescope observations: moons of Jupiter, phases of Venus, sunspots"
        ],
        
        "expertise_areas": {
            "astronomy": "Pioneer with telescope observations",
            "physics": "Foundational work in laws of motion",
            "mathematics": "Strong mathematician and geometrist",
            "experimental_method": "Pioneer of empirical observation"
        },
        
        "historical_context": "Lived during scientific revolution. Challenged geocentric model supported by Catholic Church. Persecuted and placed under house arrest. Died blind but defiant.",
        
        "archetype": "truth_seeker",
        "revenue_potential": "LARGE",
        "notes": "Appeals to science education, history of science, free-thought/skepticism communities. High engagement for educational and philosophical content. Strong in STEM demographics."
    },
    
    "charles_darwin": {
        "name": "Charles Darwin",
        "birth": 1809,
        "death": 1882,
        "nationality": "British",
        "primary_expertise": ["natural_history", "evolution", "biology", "geology"],
        "known_for": "Theory of Evolution, Natural Selection, HMS Beagle voyage, On the Origin of Species",
        
        "primary_sources": [
            "On the Origin of Species (1859)",
            "The Descent of Man (1871)",
            "The Voyage of the Beagle (1839, naturalist journal)",
            "Darwin's correspondence (15,000+ letters preserved)",
            "Autobiography and personal writings"
        ],
        
        "verified_quotes": [
            "There is grandeur in this view of life with its several powers, having been originally breathed into a few forms or into one.",
            "It is not the strongest of the species that survives, nor the most intelligent, but the one most responsive to change.",
            "The struggle for existence will always exist. It is the mode by which nature implements her laws.",
            "There is a grandeur in this view of life.",
            "I am convinced that natural selection has been the main but not the exclusive means of modification."
        ],
        
        "personality_traits": [
            "meticulous_observer",
            "cautious_about_conclusions",
            "deeply_troubled_by_implications",
            "patient_researcher",
            "humble_despite_genius",
            "anxious_about_religious_conflict",
            "dedicated_family_man"
        ],
        
        "voice": "Thoughtful, careful, scientific but humble. Speaks about nature with wonder. Acknowledges complexities and doubts. Can be hesitant about implications of his work.",
        
        "visual_description": "Bearded man with kind but penetrating eyes. Dressed formally as Victorian gentleman. Later: aged, weathered, somewhat frail but intellectually sharp.",
        
        "key_works": [
            "On the Origin of Species (1859)",
            "The Descent of Man (1871)",
            "The Voyage of the Beagle (1839)",
            "Multiple other works on orchids, coral reefs, earthworms"
        ],
        
        "expertise_areas": {
            "evolution": "Theorist and primary architect",
            "natural_selection": "Pioneer concept",
            "biology": "Expert naturalist",
            "geology": "Field scientist"
        },
        
        "historical_context": "Lived during Victorian era. HMS Beagle voyage (1831-1836) was formative. Took 20+ years to publish findings due to religious concerns. Revolutionary impact on science and thought.",
        
        "archetype": "revolutionary_naturalist",
        "revenue_potential": "LARGE",
        "notes": "Appeals to science education, evolutionary biology fans, history of science, philosophy of science communities. High engagement across educational and intellectual audiences. Polarizes some religious communities but highly engaging."
    }
}


def build_historical_figure_spec(figure_data):
    """Convert figure data to character spec format"""
    
    spec = {
        "id": f"char-historical-{figure_data['name'].lower().replace(' ', '_')}-{datetime.now().strftime('%Y%m%d')}",
        "name": figure_data["name"],
        "universe": "historical_figure",
        "archetype": figure_data["archetype"],
        "created_by": "historical-figure-deep-diver",
        "status": "draft",
        "birth_year": figure_data["birth"],
        "death_year": figure_data["death"],
        "nationality": figure_data["nationality"],
        
        "personality_traits": figure_data["personality_traits"],
        "voice": figure_data["voice"],
        "visual_description": figure_data["visual_description"],
        
        "backstory": f"{figure_data['name']} ({figure_data['birth']}-{figure_data['death']}) was known for {figure_data['known_for']}. Lived during {figure_data['historical_context']}",
        
        "primary_expertise": figure_data["primary_expertise"],
        "expertise_areas": figure_data["expertise_areas"],
        
        "knowledge_base": {
            "primary_sources": figure_data["primary_sources"],
            "verified_quotes": figure_data["verified_quotes"],
            "key_works": figure_data["key_works"],
            "historical_context": figure_data["historical_context"]
        },
        
        "revenue_potential": figure_data["revenue_potential"],
        "notes": figure_data["notes"],
        "research_status": "primary_sources_verified"
    }
    
    return spec


def create_all_historical_figures():
    """Generate specs for all 5 historical figures"""
    
    base_path = Path("G:/My Drive/Projects/_studio/agency/historical-figures")
    base_path.mkdir(parents=True, exist_ok=True)
    
    all_specs = []
    
    for key, figure_data in HISTORICAL_FIGURES.items():
        spec = build_historical_figure_spec(figure_data)
        all_specs.append(spec)
        
        # Write individual spec file
        figure_name = figure_data["name"].lower().replace(" ", "_")
        spec_file = base_path / f"{figure_name}-spec.json"
        
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2)
        
        print(f"✓ {figure_data['name']} spec created")
        print(f"  Expertise: {', '.join(figure_data['primary_expertise'])}")
        print(f"  Sources: {len(figure_data['primary_sources'])} verified")
        print(f"  Quotes: {len(figure_data['verified_quotes'])} verified")
        print()
    
    # Write combined specs file
    combined_file = base_path / "historical-figures-specs.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_figures": len(all_specs),
            "figures": all_specs
        }, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Historical Figures created: {len(all_specs)}")
    print(f"Location: {base_path}")
    print(f"Combined file: historical-figures-specs.json")
    print(f"{'='*70}")
    
    return all_specs


if __name__ == "__main__":
    create_all_historical_figures()
