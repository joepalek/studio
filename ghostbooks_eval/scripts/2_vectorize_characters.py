#!/usr/bin/env python3
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

BASE_DIR = Path(r"G:\My Drive\Projects\_studio\ghostbooks_eval")
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
        f.write(log_entry + "\n")


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
        doc_text = f"{char_name} ({era}): {expertise}\n\n{system_prompt}"

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
