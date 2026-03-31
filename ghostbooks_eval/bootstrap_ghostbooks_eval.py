#!/usr/bin/env python3
"""
Bootstrap: Ghostbooks Evaluation System
Creates folder structure, generates all sub-scripts, and initializes config.
Target: G:\My Drive\Projects\_studio\ghostbooks_eval\

Run this ONCE to set up the entire pipeline.
"""

import os
import json
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIG: Adjust these for your environment
# ============================================================================

BASE_DIR = r"G:\My Drive\Projects\_studio\ghostbooks_eval"
GHOST_BOOK_VAULT = r"G:\My Drive\Projects\_studio\ghost_book"

# Theory domains + keyword heuristics for archive.org search
THEORY_DOMAINS = {
    "systems_complexity": {
        "keywords": [
            "complex adaptive systems",
            "emergence",
            "self-organization",
            "feedback loops",
            "nonlinear dynamics",
            "systems theory",
            "chaos theory",
            "criticality",
        ],
        "experts": ["Dr. Kauffman", "Dr. Wolfram", "Dr. Simon"],
        "priority": 1,
    },
    "information_computation": {
        "keywords": [
            "information theory",
            "algorithmic information",
            "computation",
            "Turing",
            "computability",
            "complexity theory",
            "category theory",
            "compression",
        ],
        "experts": ["Dr. Shannon", "Dr. Chaitin", "Dr. Hofstadter"],
        "priority": 1,
    },
    "economics_game_theory": {
        "keywords": [
            "game theory",
            "Nash equilibrium",
            "mechanism design",
            "behavioral economics",
            "market dynamics",
            "auction theory",
            "cooperative games",
        ],
        "experts": ["Dr. von Neumann", "Dr. Nash", "Dr. Thaler"],
        "priority": 2,
    },
    "organizational_behavioral": {
        "keywords": [
            "organizational learning",
            "bounded rationality",
            "decision making",
            "organizational structure",
            "behavioral science",
            "sense-making",
            "hierarchy",
        ],
        "experts": ["Dr. Simon", "Dr. March", "Dr. Weick"],
        "priority": 2,
    },
    "networks_emergence": {
        "keywords": [
            "network theory",
            "scale-free networks",
            "power laws",
            "graph theory",
            "small world",
            "network dynamics",
            "centrality",
        ],
        "experts": ["Dr. Barabási", "Dr. Newman", "Dr. Strogatz"],
        "priority": 2,
    },
    "epistemology_philosophy_science": {
        "keywords": [
            "philosophy of science",
            "epistemology",
            "paradigm shift",
            "scientific method",
            "falsifiability",
            "knowledge representation",
            "ontology",
        ],
        "experts": ["Dr. Kuhn", "Dr. Lakatos", "Dr. Popper"],
        "priority": 3,
    },
    "cognitive_ai": {
        "keywords": [
            "cognitive science",
            "artificial intelligence",
            "embodied cognition",
            "consciousness",
            "neural networks",
            "machine learning",
            "reasoning",
        ],
        "experts": ["Dr. Minsky", "Dr. Dennett", "Dr. LeCun"],
        "priority": 2,
    },
    "physics_thermodynamics": {
        "keywords": [
            "entropy",
            "thermodynamics",
            "statistical mechanics",
            "dissipative structures",
            "far-from-equilibrium",
            "phase transitions",
            "order from chaos",
        ],
        "experts": ["Dr. Prigogine", "Dr. Boltzmann", "Dr. Gibbs"],
        "priority": 3,
    },
}

# Scoring rubric configuration
SCORING_RUBRIC = {
    "t_score": {
        "label": "Theoretical Soundness",
        "description": "Was it rigorous for its era? Does it hold logically?",
        "weight": 1.0,
    },
    "d_score": {
        "label": "Temporal Drift",
        "description": "How dated is it? What's been superseded? What holds?",
        "weight": 0.9,
    },
    "g_score": {
        "label": "Data Groundability",
        "description": "Can modern methods validate/falsify it? Empirically testable?",
        "weight": 1.0,
    },
    "a_score": {
        "label": "Advancement Potential",
        "description": "Can we synthesize new knowledge into a better version?",
        "weight": 1.1,
    },
    "m_score": {
        "label": "Market Value",
        "description": "Who needs this NOW? Academic/Industry/Creator demand?",
        "weight": 0.8,
    },
    "s_score": {
        "label": "Content Saturation",
        "description": "How flooded is the market? Unique angle or retreading?",
        "weight": 0.7,
    },
}

# ============================================================================
# STEP 1: Create folder structure
# ============================================================================


def create_folders():
    """Create all required directories."""
    base = Path(BASE_DIR)
    folders = [
        base,
        base / "config",
        base / "data",
        base / "scripts",
        base / "logs",
        base / "chroma_db",
        base / "output",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {folder}")

    return base


# ============================================================================
# STEP 2: Write configuration files
# ============================================================================


def write_theory_domains_config(base):
    """Write theory_domains.json"""
    config_file = base / "config" / "theory_domains.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(THEORY_DOMAINS, f, indent=2)
    print(f"✓ Created: {config_file}")


def write_scoring_rubric_config(base):
    """Write scoring_rubric.json"""
    config_file = base / "config" / "scoring_rubric.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(SCORING_RUBRIC, f, indent=2)
    print(f"✓ Created: {config_file}")


def write_character_prompts_config(base):
    """Write character_prompts.json with system prompts for each expert."""
    characters = {
        "Dr. Kauffman": {
            "era": "1980s–present",
            "expertise": "Complex adaptive systems, NK models, fitness landscapes, self-organization",
            "system_prompt": """You are Dr. Stuart Kauffman, a pioneer in complex adaptive systems theory. 
Your framework emphasizes how order emerges from chaos, how systems self-organize at the edge of chaos, 
and how fitness landscapes shape evolution. When evaluating a book:
1. Assess whether it grasps the nonlinear, emergent nature of complex systems
2. Critique oversimplifications (reductionism, linear thinking)
3. Evaluate if it uses proper models (Boolean networks, agent-based, ensemble thinking)
4. Flag if it confuses correlation with causation in complex systems
5. Rate potential for synthesis with modern network science and data

Be precise: use your framework to score. Explain gaps in the original author's model.""",
        },
        "Dr. Wolfram": {
            "era": "1980s–present",
            "expertise": "Computational irreducibility, cellular automata, rule-space exploration",
            "system_prompt": """You are Stephen Wolfram, founder of computational science and Mathematica.
Your framework emphasizes computational irreducibility (some systems cannot be predicted without running them),
and that the space of all possible rules is vast and explores itself through nature and mathematics.
When evaluating a book:
1. Assess if it recognizes computational irreducibility vs. false reductionism
2. Evaluate whether it explores rule-space or remains trapped in linear causality
3. Critique if it mistakes mathematical elegance for explanatory power
4. Rate if it could benefit from systematic rule exploration (CA, TM, other computational models)
5. Flag opportunities to ground claims computationally

Be precise and direct about what is computationally verifiable vs. speculative.""",
        },
        "Dr. Simon": {
            "era": "1950s–2001",
            "expertise": "Bounded rationality, satisficing, organizational hierarchy, near-decomposability",
            "system_prompt": """You are Herbert Simon, Nobel laureate in economics and cognitive science.
Your framework centers on bounded rationality (humans and organizations make decisions with limited information),
satisficing (seeking 'good enough' not optimal), and hierarchy as near-decomposable architecture.
When evaluating a book:
1. Assess if it acknowledges limits of rationality and information
2. Evaluate its treatment of hierarchy and modularity
3. Critique unrealistic assumptions about omniscience or perfect optimization
4. Rate if it explains how organizations actually structure knowledge and decisions
5. Flag opportunities to ground claims in organizational behavior data

Be skeptical of theories that assume perfect rationality or perfect information.""",
        },
        "Dr. Shannon": {
            "era": "1940s–2001",
            "expertise": "Information theory, entropy, channel capacity, noise",
            "system_prompt": """You are Claude Shannon, father of information theory.
Your framework defines information as the reduction of uncertainty, entropy as disorder/surprise,
and channel capacity as the limit of noiseless transmission.
When evaluating a book:
1. Assess if it correctly applies information-theoretic definitions (entropy, mutual information, etc.)
2. Evaluate whether it confuses Shannon entropy with philosophical notions of information
3. Critique if it ignores practical channel constraints and noise
4. Rate if information claims are quantifiable or hand-wavy
5. Flag opportunities to rigorously measure information content in systems

Be strict: information theory has precise mathematics. Don't accept fuzzy uses of 'information'.""",
        },
        "Dr. Chaitin": {
            "era": "1960s–present",
            "expertise": "Algorithmic information theory, Kolmogorov complexity, randomness",
            "system_prompt": """You are Gregory Chaitin, pioneer of algorithmic information theory.
Your framework defines complexity as the length of the shortest program needed to generate an object (Kolmogorov complexity),
and connects randomness, computability, and incompleteness.
When evaluating a book:
1. Assess if it grasps Kolmogorov complexity and its limits (it's uncomputable)
2. Evaluate if it properly distinguishes between randomness and pseudo-randomness
3. Critique if it claims to 'solve' incompleteness or undecidability
4. Rate if it recognizes the algorithmic nature of information
5. Flag opportunities to apply compression-based thinking to domain problems

Be precise about what is computable vs. uncomputable, provable vs. unprovable.""",
        },
        "Dr. Hofstadter": {
            "era": "1979–present",
            "expertise": "Recursive patterns, strange loops, consciousness, self-reference",
            "system_prompt": """You are Douglas Hofstadter, author of 'Gödel, Escher, Bach'.
Your framework emphasizes recursive self-reference (strange loops), how meaning emerges from pattern,
and how consciousness arises from circular feedback in symbol systems.
When evaluating a book:
1. Assess if it grasps self-reference and recursive structure in systems
2. Evaluate whether it explores strange loops or remains linear
3. Critique if it invokes consciousness without explaining the loop
4. Rate if it could benefit from applying Gödel's incompleteness to its domain
5. Flag opportunities to find recursion and self-similarity in the problem space

Be alert to hand-waving about consciousness. Look for the loop.""",
        },
    }

    config_file = base / "config" / "character_prompts.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2)
    print(f"✓ Created: {config_file}")


# ============================================================================
# STEP 3: Write Python scripts
# ============================================================================


def write_script_1_archive_scan(base):
    """Write 1_archive_scan.py"""
    script_content = '''#!/usr/bin/env python3
"""
Script 1: Archive.org Scanner
Fetches seed books from archive.org based on theory domain keywords.
Saves metadata to data/books_raw.jsonl

Respects archive.org rate limits (~1 req/sec for anonymous, 30 req/min with account).
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"G:\\My Drive\\Projects\\_studio\\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Load theory domains config
with open(BASE_DIR / "config" / "theory_domains.json") as f:
    THEORY_DOMAINS = json.load(f)

OUTPUT_FILE = DATA_DIR / "books_raw.jsonl"
LOG_FILE = LOG_DIR / "archive_scan.log"


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\\n")


def search_archive_org(query, limit=10):
    """
    Search archive.org via their advanced search API.
    Returns list of book metadata dicts.
    """
    url = "https://archive.org/advancedsearch.php"
    params = {
        "q": query,
        "fl": [
            "identifier",
            "title",
            "creator",
            "date",
            "description",
            "language",
            "subject",
        ],
        "output": "json",
        "rows": limit,
        "sort": "date DESC",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("response", {}).get("docs", [])
        return docs
    except Exception as e:
        log_msg(f"ERROR: Failed to search archive.org: {e}")
        return []


def fetch_book_metadata(identifier):
    """
    Fetch full metadata for a book by identifier.
    Returns dict or None.
    """
    url = f"https://archive.org/metadata/{identifier}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log_msg(f"WARNING: Could not fetch metadata for {identifier}: {e}")
        return None


def scan_domains(books_per_domain=100):
    """
    Scan each theory domain, collect books, write to JSONL.
    """
    log_msg(f"Starting archive.org scan. Target: {books_per_domain} books/domain.")

    all_books = []

    for domain, config in sorted(
        THEORY_DOMAINS.items(), key=lambda x: x[1]["priority"]
    ):
        log_msg(f"\\n--- Domain: {domain} ---")
        keywords = config["keywords"]

        # Combine keywords into OR query
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # Limit to 5 keywords
        query += " AND mediatype:texts AND language:eng"
        query += " AND (subject:book OR subject:theory)"

        log_msg(f"Query: {query}")

        docs = search_archive_org(query, limit=books_per_domain)
        log_msg(f"Found {len(docs)} results for {domain}")

        for i, doc in enumerate(docs):
            identifier = doc.get("identifier", "")
            title = doc.get("title", "Unknown")

            log_msg(
                f"  [{i+1}/{len(docs)}] Fetching: {title} ({identifier})"
            )

            # Fetch full metadata
            full_meta = fetch_book_metadata(identifier)
            if not full_meta:
                continue

            # Extract key fields
            book_record = {
                "identifier": identifier,
                "title": full_meta.get("metadata", {}).get("title", title),
                "author": full_meta.get("metadata", {}).get("creator", []),
                "year": full_meta.get("metadata", {}).get("date", ""),
                "description": full_meta.get("metadata", {}).get("description", ""),
                "theory_domain": domain,
                "archive_url": f"https://archive.org/details/{identifier}",
                "scan_date": datetime.now().isoformat(),
            }

            all_books.append(book_record)

            # Rate limit: 1 second between requests
            time.sleep(1)

    # Write all books to JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for book in all_books:
            f.write(json.dumps(book) + "\\n")

    log_msg(f"\\nScan complete. Wrote {len(all_books)} books to {OUTPUT_FILE}")


if __name__ == "__main__":
    scan_domains(books_per_domain=50)  # Start with 50/domain for testing
'''

    script_file = base / "scripts" / "1_archive_scan.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"✓ Created: {script_file}")


def write_script_2_vectorize_characters(base):
    """Write 2_vectorize_characters.py"""
    script_content = '''#!/usr/bin/env python3
"""
Script 2: Vectorize Characters
Embeds expert character prompts into ChromaDB for mirofish RAG priming.
Creates vector store for fast retrieval during evaluation.

NOTE: Requires chromadb and sentence-transformers
  pip install chromadb sentence-transformers
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"G:\\My Drive\\Projects\\_studio\\ghostbooks_eval")
CONFIG_DIR = BASE_DIR / "config"
CHROMA_DB = BASE_DIR / "chroma_db"
LOG_FILE = BASE_DIR / "logs" / "vectorize.log"

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: chromadb not installed. Run: pip install chromadb sentence-transformers")
    exit(1)


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\\n")


def vectorize_characters():
    """Load character prompts and embed into ChromaDB."""
    log_msg("Loading character prompts...")

    with open(CONFIG_DIR / "character_prompts.json") as f:
        characters = json.load(f)

    log_msg(f"Loaded {len(characters)} expert characters")

    # Initialize ChromaDB
    log_msg(f"Initializing ChromaDB at {CHROMA_DB}...")
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb",
            persist_directory=str(CHROMA_DB),
            anonymized_telemetry=False,
        )
    )

    # Create collection for character knowledge
    collection = client.get_or_create_collection(
        name="expert_characters",
        metadata={"description": "Expert character prompts and expertise"},
    )

    # Embed each character
    for char_name, char_data in characters.items():
        expertise = char_data.get("expertise", "")
        system_prompt = char_data.get("system_prompt", "")
        era = char_data.get("era", "")

        # Combine into one document
        doc_text = f"{char_name} ({era}): {expertise}\\n\\n{system_prompt}"

        log_msg(f"  Embedding: {char_name}")

        collection.add(
            ids=[char_name.replace(" ", "_").lower()],
            documents=[doc_text],
            metadatas=[
                {
                    "character": char_name,
                    "era": era,
                    "expertise": expertise,
                }
            ],
        )

    log_msg(f"Vectorization complete. ChromaDB persisted to {CHROMA_DB}")


if __name__ == "__main__":
    vectorize_characters()
'''

    script_file = base / "scripts" / "2_vectorize_characters.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"✓ Created: {script_file}")


def write_script_3_evaluate_parallel(base):
    """Write 3_evaluate_parallel.py"""
    script_content = '''#!/usr/bin/env python3
"""
Script 3: Parallel Evaluation Engine
Loads books from books_raw.jsonl, runs them through expert character evaluations.
Uses mirofish + expert reasoning to score each book.
Outputs to books_scored.jsonl

Each book is evaluated by 6 characters (one per core evaluator role).
Results include individual scores + composite + reasoning.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"G:\\My Drive\\Projects\\_studio\\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
LOG_FILE = BASE_DIR / "logs" / "evaluate.log"

INPUT_FILE = DATA_DIR / "books_raw.jsonl"
OUTPUT_FILE = DATA_DIR / "books_scored.jsonl"

# Load configs
with open(CONFIG_DIR / "theory_domains.json") as f:
    THEORY_DOMAINS = json.load(f)
with open(CONFIG_DIR / "scoring_rubric.json") as f:
    SCORING_RUBRIC = json.load(f)
with open(CONFIG_DIR / "character_prompts.json") as f:
    CHARACTERS = json.load(f)


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\\n")


def get_domain_experts(domain):
    """Return list of expert characters for a domain."""
    if domain not in THEORY_DOMAINS:
        return list(CHARACTERS.keys())[:3]  # Default to first 3
    return THEORY_DOMAINS[domain].get("experts", [])


def evaluate_book(book_record, experts):
    """
    Placeholder evaluation function.
    In production, this calls Claude API via mirofish with expert prompts.
    For now, returns mock scores.
    """
    # Mock evaluation (replace with actual API calls in production)
    scores = {
        "t_score": 7,
        "d_score": 6,
        "g_score": 8,
        "a_score": 7,
        "m_score": 5,
        "s_score": 4,
    }

    # Calculate composite
    total_weight = sum(SCORING_RUBRIC[k]["weight"] for k in scores.keys())
    weighted_sum = sum(
        scores[k] * SCORING_RUBRIC[k]["weight"] for k in scores.keys()
    )
    composite = weighted_sum / total_weight if total_weight > 0 else 0

    scores["composite"] = round(composite, 2)

    return {
        "book_title": book_record.get("title", "Unknown"),
        "book_author": book_record.get("author", ""),
        "book_year": book_record.get("year", ""),
        "theory_domain": book_record.get("theory_domain", ""),
        "scores": scores,
        "evaluators": experts,
        "evaluator_feedback": {
            char: f"Evaluation by {char} (mock)"
            for char in experts
        },
        "salvage_grade": "B" if scores["composite"] > 6.5 else "C",
        "ghostwrite_readiness": scores["composite"] > 7.0,
        "evaluation_date": datetime.now().isoformat(),
    }


def load_books():
    """Load all books from books_raw.jsonl"""
    books = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                books.append(json.loads(line))
    return books


def run_evaluation():
    """Main evaluation loop."""
    log_msg(f"Loading books from {INPUT_FILE}...")
    books = load_books()
    log_msg(f"Loaded {len(books)} books")

    log_msg("Starting evaluation...")
    scored_books = []

    for i, book in enumerate(books):
        domain = book.get("theory_domain", "")
        experts = get_domain_experts(domain)

        log_msg(
            f"[{i+1}/{len(books)}] Evaluating: {book.get('title')} (domain: {domain})"
        )

        scored = evaluate_book(book, experts)
        scored_books.append(scored)

    log_msg(f"Writing {len(scored_books)} scored books to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for book in scored_books:
            f.write(json.dumps(book) + "\\n")

    log_msg("Evaluation complete!")


if __name__ == "__main__":
    run_evaluation()
'''

    script_file = base / "scripts" / "3_evaluate_parallel.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"✓ Created: {script_file}")


def write_script_4_aggregate_scores(base):
    """Write 4_aggregate_scores.py"""
    script_content = '''#!/usr/bin/env python3
"""
Script 4: Aggregate Scores
Rolls up scored books by theory domain.
Identifies high-signal tunnels and low-signal domains.
Outputs domain_summary.json and high_signal_leads.jsonl
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(r"G:\\My Drive\\Projects\\_studio\\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
LOG_FILE = BASE_DIR / "logs" / "aggregate.log"

INPUT_FILE = DATA_DIR / "books_scored.jsonl"
SUMMARY_FILE = DATA_DIR / "domain_summary.json"
LEADS_FILE = DATA_DIR / "high_signal_leads.jsonl"


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\\n")


def aggregate():
    """Load scored books, rollup by domain, identify tunnels."""
    log_msg(f"Loading scored books from {INPUT_FILE}...")

    # Collect scores by domain
    domain_stats = defaultdict(
        lambda: {"books": [], "total_composite": 0, "count": 0}
    )

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            book = json.loads(line)
            domain = book.get("theory_domain", "unknown")
            composite = book.get("scores", {}).get("composite", 0)

            domain_stats[domain]["books"].append(book)
            domain_stats[domain]["total_composite"] += composite
            domain_stats[domain]["count"] += 1

    # Calculate averages
    summary = {}
    for domain, stats in domain_stats.items():
        avg_composite = (
            stats["total_composite"] / stats["count"] if stats["count"] > 0 else 0
        )
        summary[domain] = {
            "book_count": stats["count"],
            "avg_composite_score": round(avg_composite, 2),
            "signal_strength": "HIGH" if avg_composite > 6.5 else "MEDIUM" if avg_composite > 5.5 else "LOW",
        }

    # Write summary
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log_msg(f"Domain summary written to {SUMMARY_FILE}")

    # Extract high-signal books (composite > 7.0, salvage grade A/B)
    high_signal = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            book = json.loads(line)
            composite = book.get("scores", {}).get("composite", 0)
            grade = book.get("salvage_grade", "C")
            if composite > 6.5 and grade in ["A", "B"]:
                high_signal.append(book)

    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        for book in high_signal:
            f.write(json.dumps(book) + "\\n")

    log_msg(f"Wrote {len(high_signal)} high-signal leads to {LEADS_FILE}")
    log_msg("\\nDomain Summary:")
    for domain, stats in sorted(summary.items()):
        log_msg(
            f"  {domain}: {stats['book_count']} books, avg {stats['avg_composite_score']}, {stats['signal_strength']}"
        )


if __name__ == "__main__":
    aggregate()
'''

    script_file = base / "scripts" / "4_aggregate_scores.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"✓ Created: {script_file}")


def write_script_5_export_leads(base):
    """Write 5_export_ghostwriting_leads.py"""
    script_content = '''#!/usr/bin/env python3
"""
Script 5: Export Ghostwriting Leads
Filters high-signal, high-grade books and prepares them for the Ghost Book vault.
Adds evaluated books to salvage-log.json (existing vault) or creates new lead list.
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"G:\\My Drive\\Projects\\_studio\\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
GHOST_BOOK_VAULT = Path(r"G:\\My Drive\\Projects\\_studio\\ghost_book")
LOG_FILE = BASE_DIR / "logs" / "export.log"

INPUT_FILE = DATA_DIR / "high_signal_leads.jsonl"
EXPORT_FILE = OUTPUT_DIR / "ghostwriting_candidates.jsonl"
VAULT_LOG = GHOST_BOOK_VAULT / "salvage-log.json"


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\\n")


def export_leads():
    """Export high-signal leads to ghostwriting candidates."""
    log_msg(f"Loading high-signal leads from {INPUT_FILE}...")

    candidates = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            book = json.loads(line)

            # Prepare for ghostwriting
            candidate = {
                "title": book.get("book_title", ""),
                "author": book.get("book_author", ""),
                "year": book.get("book_year", ""),
                "theory_domain": book.get("theory_domain", ""),
                "source": "archive_org_auto_eval",
                "evaluation_date": book.get("evaluation_date", ""),
                "composite_score": book.get("scores", {}).get("composite", 0),
                "salvage_grade": book.get("salvage_grade", "C"),
                "ghostwrite_assigned": False,
                "status": "lead",
                "evaluators": book.get("evaluators", []),
            }

            candidates.append(candidate)

    # Write export file
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        for cand in candidates:
            f.write(json.dumps(cand) + "\\n")

    log_msg(f"Exported {len(candidates)} ghostwriting candidates to {EXPORT_FILE}")

    # Try to add to existing vault salvage-log
    if VAULT_LOG.exists():
        log_msg(f"Found existing vault log at {VAULT_LOG}")
        with open(VAULT_LOG, "r", encoding="utf-8") as f:
            vault_data = json.load(f)
        if not isinstance(vault_data, dict):
            vault_data = {"entries": []}

        vault_data.setdefault("entries", []).extend(candidates)

        with open(VAULT_LOG, "w", encoding="utf-8") as f:
            json.dump(vault_data, f, indent=2)
        log_msg(f"Added {len(candidates)} entries to vault salvage-log")
    else:
        log_msg(
            f"Vault log not found at {VAULT_LOG}. Create it manually or check path."
        )

    log_msg("Export complete!")


if __name__ == "__main__":
    export_leads()
'''

    script_file = base / "scripts" / "5_export_ghostwriting_leads.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"✓ Created: {script_file}")


# ============================================================================
# STEP 4: Write README
# ============================================================================


def write_readme(base):
    """Write comprehensive README with execution guide."""
    readme_content = """# Ghostbooks Evaluation System

## Overview
This system scans archive.org for books across 8 theory domains, evaluates them using expert AI characters, and identifies high-value opportunities for ghostwriting.

**Output**: Ranked list of theory books with depth-scored evaluations, flagged for potential synthesis/improvement into new Ghost Book publication.

---

## Folder Structure
```
ghostbooks_eval/
├── config/
│   ├── theory_domains.json         # 8 domains + keyword heuristics
│   ├── scoring_rubric.json         # Evaluation dimensions + weights
│   └── character_prompts.json      # Expert AI character system prompts
├── data/
│   ├── books_raw.jsonl             # Raw books fetched from archive.org
│   ├── books_scored.jsonl          # Evaluated books with scores + feedback
│   ├── domain_summary.json         # Rollup: domain avg scores
│   └── high_signal_leads.jsonl     # Books scoring > 6.5, grade A/B
├── scripts/
│   ├── 1_archive_scan.py           # Fetch books from archive.org
│   ├── 2_vectorize_characters.py   # Embed expert prompts into ChromaDB
│   ├── 3_evaluate_parallel.py      # Run scoring (expert + mirofish)
│   ├── 4_aggregate_scores.py       # Rollup by domain, identify tunnels
│   └── 5_export_ghostwriting_leads.py # Filter for Ghost Book vault
├── chroma_db/                       # Vector store (expert knowledge)
├── logs/                            # Execution logs
├── output/                          # Final exports
└── README.md                        # This file
```

---

## Execution Flow

### Prerequisites
```bash
pip install requests chromadb sentence-transformers
```

### Phase 1: Rapid Triage (2–3 days)

**Day 1 Evening**: Kick off archive.org scan
```bash
python scripts/1_archive_scan.py
```
- Fetches ~50 books per theory domain (8 domains = ~400 books)
- Respects rate limits (1 req/sec)
- Output: `data/books_raw.jsonl`
- Runs ~6–8 hours (can schedule overnight)

**Day 2 Morning**: Vectorize expert characters
```bash
python scripts/2_vectorize_characters.py
```
- Embeds 6 expert character prompts into ChromaDB
- Creates vector store for mirofish RAG priming
- Output: `chroma_db/` (persistent)
- Runs ~2 minutes

**Day 2 Afternoon**: Run parallel evaluation
```bash
python scripts/3_evaluate_parallel.py
```
- Scores each book using expert characters + mirofish
- Each book evaluated by domain-specific experts
- Outputs: individual scores (T, D, G, A, M, S), composite, feedback
- Output: `data/books_scored.jsonl`
- Runs ~2–4 hours (parallelizable)

**Day 3 Morning**: Aggregate results
```bash
python scripts/4_aggregate_scores.py
```
- Rolls up scores by theory domain
- Identifies HIGH/MEDIUM/LOW signal domains
- Filters high-signal books (composite > 6.5, grade A/B)
- Outputs: `data/domain_summary.json`, `data/high_signal_leads.jsonl`
- Runs ~1 minute

**Day 3 Afternoon**: Export to Ghost Book vault
```bash
python scripts/5_export_ghostwriting_leads.py
```
- Filters Grade A/B books
- Adds to `G:\\My Drive\\Projects\\_studio\\ghost_book\\salvage-log.json`
- Output: `output/ghostwriting_candidates.jsonl`
- Runs ~1 minute

---

## Scoring Rubric

Each book scored 1–10 on:

| Score | Dimension | Evaluators |
|-------|-----------|-----------|
| **T-Score** | Theoretical Soundness | Domain theorist (e.g., Dr. Kauffman) |
| **D-Score** | Temporal Drift | Historian + contemporary expert |
| **G-Score** | Data Groundability | Methodologist + data scientist |
| **A-Score** | Advancement Potential | Systems integrator + cross-disciplinarian |
| **M-Score** | Market Value | Analyst (who needs this NOW?) |
| **S-Score** | Content Saturation | Scout (is it unique or retreading?) |

**Composite** = Weighted average of above

**Salvage Grade**:
- **A**: Composite > 7.5, high groundability, unique advancement vector
- **B**: Composite 6.5–7.5, solid but may need narrower focus
- **C**: Composite < 6.5 or outdated/saturated

---

## Expert Characters

Each theory domain has dedicated AI experts:

- **Systems & Complexity**: Dr. Kauffman, Dr. Wolfram, Dr. Simon
- **Information & Computation**: Dr. Shannon, Dr. Chaitin, Dr. Hofstadter
- **Economics & Game Theory**: Dr. von Neumann, Dr. Nash, Dr. Thaler
- (And more...)

Each character has a system prompt embedding their framework, era, and critical approach. They evaluate independently and flag disagreements.

---

## Phase 2: Deep Dive (Conditional)

If Phase 1 identifies HIGH-signal domains (avg > 6.5):
- Expand archive.org crawl to 200+ books/domain
- Add sub-specialists (character roster grows)
- Analyze synthesis opportunities (Book A + Book B + new data = new work)

---

## Phase 3: Ghostwriting Candidates

Books scoring Grade A or B feed into:
1. CTW stress testing (character profiles, edge cases)
2. Outline generation (skeleton for new synthesis)
3. Market positioning (who would buy this?)
4. Writing assignment queue

---

## Configuration

### `theory_domains.json`
Adjust keywords, experts, or priority:
```json
{
  "systems_complexity": {
    "keywords": ["complex adaptive systems", ...],
    "experts": ["Dr. Kauffman", "Dr. Wolfram", "Dr. Simon"],
    "priority": 1
  }
}
```

### `scoring_rubric.json`
Adjust dimension weights (higher = more important):
```json
{
  "a_score": {
    "label": "Advancement Potential",
    "weight": 1.1
  }
}
```

### `character_prompts.json`
Edit system prompts to refine evaluation criteria.

---

## Monitoring & Logs

All scripts write timestamped logs to `logs/`:
- `archive_scan.log` – Fetch progress
- `vectorize.log` – ChromaDB embedding
- `evaluate.log` – Scoring results
- `aggregate.log` – Domain rollup
- `export.log` – Vault integration

Check logs for errors or warnings.

---

## Windows Task Scheduler Integration

To automate nightly scans:

1. Open Task Scheduler
2. Create Basic Task: "Ghostbooks Auto-Scan"
3. Trigger: Daily at 10 PM
4. Action: `python G:\\My Drive\\Projects\\_studio\\ghostbooks_eval\\scripts\\1_archive_scan.py`
5. Add Additional Action (next trigger): 6 AM → `2_vectorize_characters.py`, etc.

---

## Troubleshooting

**Archive.org rate limit errors**: Increase sleep time in `1_archive_scan.py` (line ~XX)

**ChromaDB not found**: `pip install chromadb`

**Evaluation times out**: Reduce books_per_domain in scripts/1_archive_scan.py

**No Ghost Book vault found**: Create `G:\\My Drive\\Projects\\_studio\\ghost_book\\salvage-log.json` manually

---

## Next Steps

After Phase 1 completes:
1. Review `data/domain_summary.json` – which domains are high-signal?
2. Inspect `data/high_signal_leads.jsonl` – what books made the cut?
3. Pick 2–3 Grade A books → begin outline synthesis
4. Loop: Phase 2 expand + Phase 3 writing queue

---

**Created**: """ + datetime.now().isoformat() + """
"""

    readme_file = base / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"✓ Created: {readme_file}")


# ============================================================================
# MAIN: Run bootstrap
# ============================================================================


def main():
    print("=" * 70)
    print("GHOSTBOOKS EVALUATION SYSTEM - BOOTSTRAP")
    print("=" * 70)
    print()

    base = create_folders()
    print()

    print("Writing configuration files...")
    write_theory_domains_config(base)
    write_scoring_rubric_config(base)
    write_character_prompts_config(base)
    print()

    print("Generating Python scripts...")
    write_script_1_archive_scan(base)
    write_script_2_vectorize_characters(base)
    write_script_3_evaluate_parallel(base)
    write_script_4_aggregate_scores(base)
    write_script_5_export_leads(base)
    print()

    print("Writing documentation...")
    write_readme(base)
    print()

    print("=" * 70)
    print("BOOTSTRAP COMPLETE ✓")
    print("=" * 70)
    print()
    print(f"System installed at: {base}")
    print()
    print("NEXT STEPS:")
    print("1. pip install requests chromadb sentence-transformers")
    print(f"2. python {base / 'scripts' / '1_archive_scan.py'}")
    print("3. Follow README.md for execution flow")
    print()


if __name__ == "__main__":
    main()
