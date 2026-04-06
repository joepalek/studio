"""
Track 5: Molded-Mark OCR
Detects molded marks using EasyOCR (free, multi-language)

Molded marks appear on:
  - Pottery bottoms
  - Glass stems/bases
  - Ceramic glazes
  - Metal castings
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
from consensus_engine import TrackResult

class MoldedOCR:
    """
    Molded mark detection using EasyOCR (free, multi-language)
    
    Advantages:
    - Multi-language support
    - Better on rotated/distorted text
    - Simpler API than PaddleOCR
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.reader = None
        self._init_easyocr()
        logger.info('MoldedOCR initialized (EasyOCR)')
    
    def _init_easyocr(self):
        """Initialize EasyOCR reader."""
        try:
            import easyocr
            logger.info('Loading EasyOCR model...')
            self.reader = easyocr.Reader(['en'], gpu=False)
            logger.info('✓ EasyOCR ready')
        except ImportError:
            logger.warning('easyocr not installed, using mock implementation')
            self.reader = None
        except Exception as e:
            logger.warning(f'EasyOCR init failed: {e}, using mock')
            self.reader = None
    
    def extract(self, image_path: str, item_id: str = "item_001") -> TrackResult:
        """
        Extract molded marks from image.
        
        Args:
            image_path: Path to image file
            item_id: Item identifier
            
        Returns:
            TrackResult with molded mark findings
        """
        logger.info(f'Track 5: Extracting molded marks from {image_path}')
        
        try:
            if not Path(image_path).exists():
                logger.warning(f'Image not found: {image_path}')
                return TrackResult(
                    track_num=5,
                    track_name="Molded OCR",
                    title_candidate="FILE_NOT_FOUND",
                    confidence=0.0
                )
            
            if self.reader:
                return self._extract_with_easyocr(image_path, item_id)
            else:
                return self._extract_mock(image_path, item_id)
        
        except Exception as e:
            logger.error(f'Track 5 error: {e}')
            return TrackResult(
                track_num=5,
                track_name="Molded OCR",
                title_candidate="ERROR",
                confidence=0.0,
                notes=str(e)
            )
    
    def _extract_with_easyocr(self, image_path: str, item_id: str) -> TrackResult:
        """Extract using actual EasyOCR."""
        logger.debug(f'EasyOCR analyzing {image_path}')
        
        try:
            # Run OCR
            results = self.reader.readtext(image_path)
            
            # Parse results
            marks = []
            for detection in results:
                text = detection[1]
                conf = detection[2]
                
                # Filter for likely marks (usually short text, high confidence)
                if conf > 0.6 and len(text) > 1 and len(text) < 50:
                    marks.append((text, conf))
                    logger.debug(f'Found mark: {text} (conf: {conf:.2f})')
            
            if marks:
                # Get best confidence
                best_mark = max(marks, key=lambda x: x[1])
                
                return TrackResult(
                    track_num=5,
                    track_name="Molded OCR",
                    title_candidate=best_mark[0],
                    maker=self._parse_maker(best_mark[0]),
                    confidence=best_mark[1],
                    notes=f"Found {len(marks)} molded mark(s)"
                )
            else:
                logger.info('No molded marks detected')
                return TrackResult(
                    track_num=5,
                    track_name="Molded OCR",
                    title_candidate="NO_MARK",
                    confidence=0.2,
                    notes="No readable molded marks found"
                )
        
        except Exception as e:
            logger.error(f'EasyOCR error: {e}')
            return TrackResult(
                track_num=5,
                track_name="Molded OCR",
                title_candidate="ERROR",
                confidence=0.0,
                notes=str(e)
            )
    
    def _extract_mock(self, image_path: str, item_id: str) -> TrackResult:
        """Mock molded mark extraction for testing."""
        import time
        time.sleep(0.2)
        
        return TrackResult(
            track_num=5,
            track_name="Molded OCR",
            title_candidate="Made in Italy",
            maker="Italy",
            confidence=0.81,
            notes="Mock mark (EasyOCR not available)"
        )
    
    def _parse_maker(self, mark_text: str) -> Optional[str]:
        """Extract maker from molded mark."""
        text = mark_text.upper()
        
        # Common patterns
        makers = {
            'MADE IN': 'Made in',
            'ITALY': 'Italy',
            'FRANCE': 'France',
            'GERMANY': 'Germany',
            'ENGLAND': 'England',
            'JAPAN': 'Japan',
            'MURANO': 'Murano',
        }
        
        for key, maker in makers.items():
            if key in text:
                return maker
        
        return mark_text[:30] if mark_text else None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    ocr = MoldedOCR()
    result = ocr.extract('/mock/test.jpg')
    
    print(f"\nMark: {result.title_candidate}")
    print(f"Maker: {result.maker}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Notes: {result.notes}\n")
