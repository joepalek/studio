"""
Track 3: Hallmark OCR
Detects and reads maker hallmarks using PaddleOCR (free, open-source)

Hallmarks appear on:
  - Pottery/ceramics (bottom marking)
  - Glass (etched or molded)
  - Metal (stamped)
  - Wood (engraved)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
from consensus_engine import TrackResult

class HallmarkOCR:
    """
    Hallmark detection using PaddleOCR (free tier)
    Identifies maker marks, country of origin, dates, etc.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.ocr = None
        self._init_paddle_ocr()
        logger.info('HallmarkOCR initialized (PaddleOCR)')
    
    def _init_paddle_ocr(self):
        """Initialize PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR
            logger.info('Loading PaddleOCR model...')
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info('✓ PaddleOCR ready')
        except ImportError:
            logger.warning('paddleocr not installed, using mock implementation')
            self.ocr = None
        except Exception as e:
            logger.warning(f'PaddleOCR init failed: {e}, using mock')
            self.ocr = None
    
    def extract(self, image_path: str, item_id: str = "item_001") -> TrackResult:
        """
        Extract hallmarks from image.
        
        Args:
            image_path: Path to image
            item_id: Item identifier
            
        Returns:
            TrackResult with hallmark findings
        """
        logger.info(f'Track 3: Extracting hallmarks from {image_path}')
        
        try:
            if not Path(image_path).exists():
                logger.warning(f'Image not found: {image_path}')
                return TrackResult(
                    track_num=3,
                    track_name="Hallmark OCR",
                    title_candidate="FILE_NOT_FOUND",
                    confidence=0.0
                )
            
            if self.ocr:
                return self._extract_with_paddle(image_path, item_id)
            else:
                return self._extract_mock(image_path, item_id)
        
        except Exception as e:
            logger.error(f'Track 3 error: {e}')
            return TrackResult(
                track_num=3,
                track_name="Hallmark OCR",
                title_candidate="ERROR",
                confidence=0.0,
                notes=str(e)
            )
    
    def _extract_with_paddle(self, image_path: str, item_id: str) -> TrackResult:
        """Extract using actual PaddleOCR."""
        import cv2
        
        logger.debug(f'PaddleOCR analyzing {image_path}')
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return TrackResult(
                    track_num=3,
                    track_name="Hallmark OCR",
                    title_candidate="CANNOT_READ_IMAGE",
                    confidence=0.0
                )
            
            # Run OCR
            result = self.ocr.ocr(image_path, cls=True)
            
            # Parse results
            hallmarks = []
            for line in result:
                if line:
                    for word_info in line:
                        text = word_info[1][0]
                        conf = word_info[1][1]
                        
                        # Look for maker marks
                        if self._is_hallmark_text(text) and conf > 0.5:
                            hallmarks.append((text, conf))
                            logger.debug(f'Found hallmark: {text} (conf: {conf:.2f})')
            
            if hallmarks:
                best_hallmark = max(hallmarks, key=lambda x: x[1])
                return TrackResult(
                    track_num=3,
                    track_name="Hallmark OCR",
                    title_candidate=best_hallmark[0],
                    maker=self._parse_maker(best_hallmark[0]),
                    confidence=best_hallmark[1],
                    notes=f"Found {len(hallmarks)} hallmark(s)"
                )
            else:
                logger.info('No hallmarks detected')
                return TrackResult(
                    track_num=3,
                    track_name="Hallmark OCR",
                    title_candidate="NO_HALLMARK",
                    confidence=0.3,
                    notes="No readable hallmarks found"
                )
        
        except Exception as e:
            logger.error(f'PaddleOCR error: {e}')
            return TrackResult(
                track_num=3,
                track_name="Hallmark OCR",
                title_candidate="ERROR",
                confidence=0.0,
                notes=str(e)
            )
    
    def _extract_mock(self, image_path: str, item_id: str) -> TrackResult:
        """Mock hallmark extraction for testing."""
        import time
        time.sleep(0.2)
        
        return TrackResult(
            track_num=3,
            track_name="Hallmark OCR",
            title_candidate="Murano Italy Mark",
            maker="Murano",
            confidence=0.88,
            notes="Mock hallmark (PaddleOCR not available)"
        )
    
    def _is_hallmark_text(self, text: str) -> bool:
        """Check if text looks like a hallmark."""
        if not text or len(text) < 2:
            return False
        
        # Common hallmark patterns
        hallmark_indicators = [
            'made in',
            'italy',
            'france',
            'germany',
            'england',
            'murano',
            'mark',
            '©',
            'ltd',
            'inc',
            'co',
            'pat',
            'reg',
            'trademark'
        ]
        
        text_lower = text.lower()
        return any(ind in text_lower for ind in hallmark_indicators)
    
    def _parse_maker(self, hallmark_text: str) -> Optional[str]:
        """Extract maker name from hallmark text."""
        # Simple extraction - in production would use NER
        text = hallmark_text.upper()
        
        makers = {
            'MURANO': 'Murano',
            'ITALY': 'Italy',
            'FRANCE': 'France',
            'GERMANY': 'Germany',
            'ENGLAND': 'England',
        }
        
        for key, maker in makers.items():
            if key in text:
                return maker
        
        return hallmark_text[:30] if len(hallmark_text) > 0 else None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    ocr = HallmarkOCR()
    result = ocr.extract('/mock/test.jpg')
    
    print(f"\nHallmark: {result.title_candidate}")
    print(f"Maker: {result.maker}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Notes: {result.notes}\n")
