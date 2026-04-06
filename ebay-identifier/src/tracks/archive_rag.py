"""
Track 4: Archive RAG
Searches eBay sold history + auction archive via ChromaDB (free, embedded)

Builds vector index from:
  - eBay sold listings (title + description)
  - Your own past sales
  - Public auction databases
  - Estate inventory archives
"""

import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
from consensus_engine import TrackResult

class ArchiveRAG:
    """
    Archive RAG lookup using ChromaDB (free, embedded vector DB)
    
    Searches against:
      - eBay sold inventory
      - Historical archives
      - Your own past sales history
      - Auction results
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.client = None
        self.collection = None
        self._init_chromadb()
        logger.info('ArchiveRAG initialized (ChromaDB)')
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            
            # Create persistent client
            self.client = chromadb.Client()
            
            # Create collection for eBay archive
            self.collection = self.client.get_or_create_collection(
                name="ebay_archive",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info('✓ ChromaDB ready')
            
            # Check if collection has data
            count = self.collection.count()
            logger.info(f'Archive has {count} indexed items')
            
            if count == 0:
                logger.info('Archive empty - initializing with sample data...')
                self._initialize_sample_data()
        
        except ImportError:
            logger.warning('chromadb not installed, using mock implementation')
            self.client = None
        except Exception as e:
            logger.warning(f'ChromaDB init failed: {e}')
            self.client = None
    
    def _initialize_sample_data(self):
        """Initialize with sample eBay sold data."""
        try:
            import random
            
            sample_items = [
                {"title": "Murano glass vase 1960s", "category": "glass", "maker": "Murano"},
                {"title": "Vintage murano blown glass", "category": "glass", "maker": "Murano"},
                {"title": "Italian glass vase mid century", "category": "glass", "maker": "Italy"},
                {"title": "Retro ceramic pottery bowl", "category": "pottery", "maker": "Unknown"},
                {"title": "Depression glass Depression Era", "category": "glass", "maker": "Depression"},
                {"title": "Vintage estate jewelry brooch", "category": "jewelry", "maker": "Vintage"},
                {"title": "Antique porcelain doll German", "category": "doll", "maker": "Germany"},
                {"title": "Vintage sports card collection", "category": "collectible", "maker": "Card"},
                {"title": "MCM modern chair eames style", "category": "furniture", "maker": "MCM"},
                {"title": "Vintage record album vinyl", "category": "music", "maker": "Vinyl"},
            ]
            
            # Add to collection
            ids = [f"sample_{i}" for i in range(len(sample_items))]
            documents = [item["title"] for item in sample_items]
            metadatas = [{"category": item["category"], "maker": item["maker"]} for item in sample_items]
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f'Initialized archive with {len(sample_items)} sample items')
        
        except Exception as e:
            logger.warning(f'Sample data init failed: {e}')
    
    def search(self, query: str, item_id: str = "item_001", top_k: int = 3) -> TrackResult:
        """
        Search archive for similar items.
        
        Args:
            query: Search query (item title/description)
            item_id: Item identifier
            top_k: Number of results to return
            
        Returns:
            TrackResult with best archive match
        """
        logger.info(f'Track 4: Searching archive for "{query[:50]}..."')
        
        try:
            if self.client is None or self.collection is None:
                return self._search_mock(query, item_id)
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["metadatas", "distances"]
            )
            
            if not results or not results.get('ids') or len(results['ids'][0]) == 0:
                logger.info('No archive matches found')
                return TrackResult(
                    track_num=4,
                    track_name="Archive RAG",
                    title_candidate="NO_MATCH",
                    confidence=0.2,
                    notes="No similar items in archive"
                )
            
            # Get best match
            best_idx = 0
            best_distance = results['distances'][0][best_idx]
            best_id = results['ids'][0][best_idx]
            best_meta = results['metadatas'][0][best_idx]
            
            # Convert distance to confidence (lower distance = higher confidence)
            confidence = max(0.0, 1.0 - best_distance)
            
            logger.info(f'Track 4: Best match - {best_id} (confidence: {confidence:.2f})')
            
            return TrackResult(
                track_num=4,
                track_name="Archive RAG",
                title_candidate=best_id,
                maker=best_meta.get('maker'),
                category=best_meta.get('category'),
                confidence=confidence,
                notes=f"Best of {len(results['ids'][0])} archive matches"
            )
        
        except Exception as e:
            logger.error(f'Track 4 error: {e}')
            return TrackResult(
                track_num=4,
                track_name="Archive RAG",
                title_candidate="ERROR",
                confidence=0.0,
                notes=str(e)
            )
    
    def _search_mock(self, query: str, item_id: str) -> TrackResult:
        """Mock archive search for testing."""
        import time
        time.sleep(0.1)
        
        return TrackResult(
            track_num=4,
            track_name="Archive RAG",
            title_candidate="Archive Match - Murano Vase 1960s",
            maker="Murano",
            era="1960s",
            confidence=0.72,
            notes="Mock search (ChromaDB not available)"
        )
    
    def add_to_archive(self, title: str, description: str, maker: Optional[str] = None,
                       category: Optional[str] = None, item_id: Optional[str] = None):
        """
        Add item to archive for future searches.
        
        In production: Called after successful sales
        """
        if self.collection is None:
            logger.warning('Cannot add to archive - ChromaDB not ready')
            return False
        
        try:
            import uuid
            
            doc_id = item_id or f"item_{uuid.uuid4().hex[:8]}"
            doc_text = f"{title} {description}"
            
            self.collection.add(
                ids=[doc_id],
                documents=[doc_text],
                metadatas=[{
                    "title": title,
                    "maker": maker or "unknown",
                    "category": category or "general"
                }]
            )
            
            logger.info(f'Added to archive: {doc_id}')
            return True
        
        except Exception as e:
            logger.error(f'Failed to add to archive: {e}')
            return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    rag = ArchiveRAG()
    result = rag.search("vintage glass vase 1960s murano")
    
    print(f"\nArchive match: {result.title_candidate}")
    print(f"Maker: {result.maker}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Notes: {result.notes}\n")
