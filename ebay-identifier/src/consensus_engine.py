"""
Consensus Engine - 6-Track Consensus Logic

Combines results from 6 identification tracks:
  1. Reverse image search (Bright SEO)
  2. VLM attribute extraction (Claude)
  3. Hallmark OCR (PaddleOCR)
  4. Archive RAG lookup (ChromaDB)
  5. Molded-mark OCR (EasyOCR)
  6. Manual override (user input)

FREE-FIRST: All components are open-source or free-tier APIs
"""

import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence score classification."""
    VERY_HIGH = (0.90, 1.00)
    HIGH = (0.75, 0.90)
    MEDIUM = (0.60, 0.75)
    LOW = (0.40, 0.60)
    VERY_LOW = (0.00, 0.40)

@dataclass
class TrackResult:
    """Result from a single identification track."""
    track_num: int
    track_name: str
    title_candidate: str
    maker: Optional[str] = None
    era: Optional[str] = None
    material: Optional[str] = None
    condition: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 0.0
    notes: str = ""
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ConsensusResult:
    """Final consensus from all 6 tracks."""
    item_id: str
    title: str
    maker: Optional[str] = None
    era: Optional[str] = None
    material: Optional[str] = None
    condition: Optional[str] = None
    category: str = "general"
    confidence_score: float = 0.0
    confidence_level: str = "UNKNOWN"
    recommendation: str = "MANUAL_ONLY"
    track_results: List[TrackResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        data = asdict(self)
        data['track_results'] = [r.to_dict() for r in self.track_results]
        return data
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class ConsensusEngine:
    """
    6-track consensus engine for item identification.
    
    Tracks:
      1. Pixel Match (reverse image search)
      2. VLM Extraction (Claude vision)
      3. Hallmark OCR (PaddleOCR)
      4. Archive RAG (ChromaDB lookup)
      5. Molded-Mark OCR (EasyOCR)
      6. Manual Override (user input)
    """
    
    def __init__(self, config: Dict = None):
        """Initialize consensus engine."""
        self.config = config or {}
        self.weights = {
            1: 0.15,  # Pixel match (reverse image)
            2: 0.20,  # VLM extraction
            3: 0.20,  # Hallmark OCR
            4: 0.20,  # Archive RAG
            5: 0.15,  # Molded-mark OCR
            6: 1.0    # Manual (always wins if set)
        }
        self.results_log = []
        logger.info('ConsensusEngine initialized (6-track, free-first)')
    
    def compute_consensus(self, track_results: List[TrackResult], item_id: str = "item_001") -> ConsensusResult:
        """
        Compute final consensus from all track results.
        
        Args:
            track_results: Results from all 6 tracks
            item_id: Unique identifier for this item
            
        Returns:
            ConsensusResult with final identification
        """
        logger.info(f'Computing consensus for {item_id} from {len(track_results)} tracks')
        
        # Check for manual override (track 6)
        manual_result = next((r for r in track_results if r.track_num == 6), None)
        if manual_result and manual_result.confidence > 0.5:
            logger.info(f'Manual override detected (track 6) with confidence {manual_result.confidence}')
            consensus_result = ConsensusResult(
                item_id=item_id,
                title=manual_result.title_candidate or "MANUAL_ENTRY",
                maker=manual_result.maker,
                era=manual_result.era,
                material=manual_result.material,
                condition=manual_result.condition,
                category=manual_result.category or "manual",
                confidence_score=1.0,
                confidence_level="VERY_HIGH",
                recommendation="APPROVE",
                track_results=track_results
            )
            self.results_log.append(consensus_result)
            return consensus_result
        
        # Compute weighted consensus from all tracks
        if not track_results:
            logger.warning('No track results provided')
            return ConsensusResult(
                item_id=item_id,
                title="UNKNOWN",
                confidence_score=0.0,
                confidence_level="VERY_LOW",
                recommendation="MANUAL_ONLY",
                track_results=[]
            )
        
        # Calculate weighted score
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for result in track_results:
            if result.track_num in self.weights:
                weight = self.weights[result.track_num]
                weighted_sum += result.confidence * weight
                weight_sum += weight
        
        # Normalize
        final_confidence = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(final_confidence)
        
        # Determine recommendation
        if final_confidence >= 0.80:
            recommendation = 'APPROVE'
        elif final_confidence >= 0.60:
            recommendation = 'REVIEW'
        else:
            recommendation = 'MANUAL_ONLY'
        
        logger.info(f'Consensus: {final_confidence:.2f} ({confidence_level}) → {recommendation}')
        
        # Build result (aggregate from highest confidence)
        consensus_result = ConsensusResult(
            item_id=item_id,
            title=self._aggregate_field(track_results, 'title_candidate'),
            maker=self._aggregate_field(track_results, 'maker'),
            era=self._aggregate_field(track_results, 'era'),
            material=self._aggregate_field(track_results, 'material'),
            condition=self._aggregate_field(track_results, 'condition'),
            category=self._aggregate_field(track_results, 'category'),
            confidence_score=final_confidence,
            confidence_level=confidence_level,
            recommendation=recommendation,
            track_results=track_results
        )
        
        self.results_log.append(consensus_result)
        return consensus_result
    
    def _get_confidence_level(self, score: float) -> str:
        """Map confidence score to level."""
        for level in ConfidenceLevel:
            if level.value[0] <= score <= level.value[1]:
                return level.name
        return "VERY_LOW"
    
    def _aggregate_field(self, results: List[TrackResult], field: str) -> str:
        """Aggregate field from highest-confidence results."""
        values = []
        scores = []
        
        for r in results:
            val = getattr(r, field, None)
            if val and val != "UNKNOWN":
                values.append(val)
                scores.append(r.confidence)
        
        if not values:
            return "UNKNOWN"
        
        # Return value with highest confidence
        if scores:
            idx = scores.index(max(scores))
            return values[idx]
        
        return values[0]
    
    def get_results_summary(self) -> Dict:
        """Get summary of all results processed."""
        if not self.results_log:
            return {'total_processed': 0, 'results': []}
        
        return {
            'total_processed': len(self.results_log),
            'average_confidence': sum(r.confidence_score for r in self.results_log) / len(self.results_log),
            'recommendations': {
                'APPROVE': len([r for r in self.results_log if r.recommendation == 'APPROVE']),
                'REVIEW': len([r for r in self.results_log if r.recommendation == 'REVIEW']),
                'MANUAL_ONLY': len([r for r in self.results_log if r.recommendation == 'MANUAL_ONLY'])
            }
        }

# ============================================================================
# TESTING: Basic functionality test
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Create engine
    engine = ConsensusEngine()
    
    # Simulate 6 track results
    test_results = [
        TrackResult(1, "Reverse Image", "Vintage Glass Vase", maker="Murano", era="1960s", confidence=0.85),
        TrackResult(2, "VLM Extraction", "Glass Vase Vintage", maker="Murano", material="Blown Glass", confidence=0.80),
        TrackResult(3, "Hallmark OCR", "Murano Mark Found", maker="Murano", confidence=0.90),
        TrackResult(4, "Archive RAG", "Murano 1960s Vase", era="1960s", confidence=0.75),
        TrackResult(5, "Molded OCR", "Made in Italy", maker="Murano", confidence=0.85),
        TrackResult(6, "Manual", "", confidence=0.0)  # No manual override
    ]
    
    # Compute consensus
    result = engine.compute_consensus(test_results, "test_item_001")
    
    print("\n" + "="*60)
    print("CONSENSUS RESULT")
    print("="*60)
    print(f"Item: {result.title}")
    print(f"Maker: {result.maker}")
    print(f"Era: {result.era}")
    print(f"Material: {result.material}")
    print(f"Confidence: {result.confidence_score:.2f} ({result.confidence_level})")
    print(f"Recommendation: {result.recommendation}")
    print("="*60 + "\n")
