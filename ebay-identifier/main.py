#!/usr/bin/env python3
"""
eBay Item Identifier - Consensus Engine v2.0
Free-First Implementation

Main entry point - orchestrates identification workflow
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from consensus_engine import ConsensusEngine, TrackResult
from tracks.reverse_image import ReverseImageSearch
from tracks.vlm_extraction import VLMExtraction

# Configure logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'ebay_identifier_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class IdentificationPipeline:
    """Orchestrates the full 6-track identification pipeline."""
    
    def __init__(self):
        """Initialize all components."""
        self.engine = ConsensusEngine()
        self.track1 = ReverseImageSearch()
        self.track2 = VLMExtraction()
        logger.info('IdentificationPipeline initialized')
    
    def identify_item(self, image_path: str, item_id: str = "item_001"):
        """
        Identify item from image using full 6-track consensus.
        
        Args:
            image_path: Path to item image
            item_id: Unique item identifier
        """
        logger.info(f'\n{"="*70}')
        logger.info(f'Identifying item: {item_id}')
        logger.info(f'Image: {image_path}')
        logger.info(f'{"="*70}')
        
        # Initialize track results
        track_results = []
        
        # Track 1: Reverse Image Search
        logger.info('\n--- Track 1: Reverse Image Search ---')
        result1 = self.track1.search(image_path, item_id)
        track_results.append(result1)
        logger.info(f'Result: {result1.title_candidate} (confidence: {result1.confidence:.2f})')
        
        # Track 2: VLM Extraction
        logger.info('\n--- Track 2: VLM Attribute Extraction ---')
        vlm_result = self.track2.extract(image_path, item_id)
        result2 = TrackResult(
            track_num=2,
            track_name="VLM Extraction",
            title_candidate=vlm_result.get('title', 'UNKNOWN'),
            maker=vlm_result.get('maker'),
            era=vlm_result.get('era'),
            material=vlm_result.get('material'),
            condition=vlm_result.get('condition'),
            confidence=vlm_result.get('confidence', 0.7),
            notes=vlm_result.get('notes', '')
        )
        track_results.append(result2)
        logger.info(f'Result: {result2.title_candidate} (confidence: {result2.confidence:.2f})')
        
        # Tracks 3-5: Placeholder (to be implemented)
        logger.info('\n--- Track 3: Hallmark OCR ---')
        result3 = TrackResult(
            track_num=3,
            track_name="Hallmark OCR",
            title_candidate="",
            confidence=0.0,
            notes="Not yet implemented"
        )
        track_results.append(result3)
        
        logger.info('\n--- Track 4: Archive RAG ---')
        result4 = TrackResult(
            track_num=4,
            track_name="Archive RAG",
            title_candidate="",
            confidence=0.0,
            notes="Not yet implemented"
        )
        track_results.append(result4)
        
        logger.info('\n--- Track 5: Molded-Mark OCR ---')
        result5 = TrackResult(
            track_num=5,
            track_name="Molded-Mark OCR",
            title_candidate="",
            confidence=0.0,
            notes="Not yet implemented"
        )
        track_results.append(result5)
        
        # Track 6: Manual Override (none for now)
        logger.info('\n--- Track 6: Manual Override ---')
        result6 = TrackResult(
            track_num=6,
            track_name="Manual Override",
            title_candidate="",
            confidence=0.0,
            notes="No manual override provided"
        )
        track_results.append(result6)
        
        # Compute consensus
        logger.info('\n--- COMPUTING CONSENSUS ---')
        consensus = self.engine.compute_consensus(track_results, item_id)
        
        # Log results
        logger.info(f'\n{"="*70}')
        logger.info('FINAL RESULT')
        logger.info(f'{"="*70}')
        logger.info(f'Item ID: {consensus.item_id}')
        logger.info(f'Title: {consensus.title}')
        logger.info(f'Maker: {consensus.maker}')
        logger.info(f'Era: {consensus.era}')
        logger.info(f'Material: {consensus.material}')
        logger.info(f'Condition: {consensus.condition}')
        logger.info(f'Confidence: {consensus.confidence_score:.2f} ({consensus.confidence_level})')
        logger.info(f'Recommendation: {consensus.recommendation}')
        logger.info(f'{"="*70}\n')
        
        return consensus
    
    def test_on_sample_items(self, num_items: int = 5):
        """Test identification on sample items."""
        logger.info(f'\n\n{"#"*70}')
        logger.info(f'TEST: Identifying {num_items} sample items')
        logger.info(f'{"#"*70}\n')
        
        results = []
        
        for i in range(1, num_items + 1):
            item_id = f'test_item_{i:03d}'
            # Mock image path (doesn't need to exist for mock implementations)
            image_path = f'/mock/image_{i}.jpg'
            
            try:
                result = self.identify_item(image_path, item_id)
                results.append(result.to_dict())
            except Exception as e:
                logger.error(f'Error identifying {item_id}: {e}')
        
        # Summary
        logger.info(f'\n{"#"*70}')
        logger.info('TEST SUMMARY')
        logger.info(f'{"#"*70}')
        logger.info(f'Items tested: {len(results)}')
        logger.info(f'Average confidence: {sum(r["confidence_score"] for r in results) / len(results):.2f}')
        
        approve_count = len([r for r in results if r['recommendation'] == 'APPROVE'])
        review_count = len([r for r in results if r['recommendation'] == 'REVIEW'])
        manual_count = len([r for r in results if r['recommendation'] == 'MANUAL_ONLY'])
        
        logger.info(f'Recommendations: APPROVE={approve_count}, REVIEW={review_count}, MANUAL_ONLY={manual_count}')
        logger.info(f'{"#"*70}\n')
        
        return results

def main():
    """Main entry point."""
    logger.info('='*70)
    logger.info('eBay Item Identifier - Consensus Engine v2.0')
    logger.info('Free-First Implementation')
    logger.info('='*70)
    
    try:
        # Initialize pipeline
        pipeline = IdentificationPipeline()
        
        # Run test
        logger.info('\nStarting Phase 1 test (5 sample items)...')
        results = pipeline.test_on_sample_items(num_items=5)
        
        # Save results
        results_file = Path(__file__).parent / 'logs' / f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f'Results saved to: {results_file}')
        logger.info('\nPhase 1 test completed successfully!')
        
        return 0
    
    except KeyboardInterrupt:
        logger.info('User interrupted')
        return 1
    except Exception as e:
        logger.exception(f'Fatal error: {e}')
        return 1

if __name__ == '__main__':
    sys.exit(main())
