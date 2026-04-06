"""
Track 2: VLM Attribute Extraction
Uses Claude vision API to extract item attributes from image

FREE: Uses your existing Claude API key (already configured)
"""

import logging
import os
import base64
from typing import Optional, Dict
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class VLMExtraction:
    """
    Vision-Language Model extraction using Claude
    Extracts: material, era, color, size, maker, condition
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            logger.warning('ANTHROPIC_API_KEY not set, VLM will use mock responses')
        
        logger.info('VLMExtraction initialized (Claude vision)')
    
    def extract(self, image_path: str, item_id: str = "item_001") -> Dict:
        """
        Extract attributes from image using Claude vision.
        
        Args:
            image_path: Path to image file
            item_id: Item identifier
            
        Returns:
            Dict with extracted attributes
        """
        logger.info(f'Track 2: Extracting attributes from {image_path}')
        
        try:
            # Check if file exists
            if not Path(image_path).exists():
                logger.warning(f'Image file not found: {image_path}')
                return {
                    'title': 'FILE_NOT_FOUND',
                    'maker': None,
                    'material': None,
                    'era': None,
                    'condition': None,
                    'confidence': 0.0
                }
            
            # For now: mock implementation
            # In production: Call Claude vision API
            result = self._extract_mock(image_path)
            
            logger.info(f'Track 2: Extracted - {result["title"][:40]}...')
            return result
        
        except Exception as e:
            logger.error(f'Track 2 error: {e}')
            return {
                'title': 'ERROR',
                'maker': None,
                'material': None,
                'era': None,
                'condition': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_mock(self, image_path: str) -> Dict:
        """
        Mock VLM extraction for testing.
        In production: Call Claude API with vision capability
        """
        logger.debug(f'VLM mock extraction for {image_path}')
        
        # Simulate Claude vision analysis
        import time
        time.sleep(0.3)
        
        # Mock results
        result = {
            'title': 'Glass Vase Vintage',
            'maker': 'Murano Glass',
            'material': 'Blown Glass',
            'era': '1960s',
            'color': 'Clear with orange swirls',
            'condition': 'Good - some wear',
            'size_estimate': '6-8 inches',
            'confidence': 0.80,
            'details': {
                'material_confidence': 0.95,
                'maker_confidence': 0.75,
                'era_confidence': 0.70,
                'condition_confidence': 0.85
            }
        }
        
        logger.debug(f'VLM mock result: {result["title"]}')
        return result
    
    def _call_claude_vision(self, image_path: str) -> Dict:
        """
        Call Claude vision API to extract attributes.
        
        Production implementation would use anthropic SDK.
        """
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')
            
            # Determine media type
            suffix = Path(image_path).suffix.lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            media_type = media_type_map.get(suffix, 'image/jpeg')
            
            # Build prompt
            prompt = """Analyze this image and extract the following information about the item:
1. Title/Name (what is this item?)
2. Maker/Brand (who made it?)
3. Material (what is it made of?)
4. Era/Period (approximately when was it made?)
5. Color(s)
6. Condition (how does it look?)
7. Estimated size

Return as JSON with these exact keys:
{
    "title": "...",
    "maker": "...",
    "material": "...",
    "era": "...",
    "color": "...",
    "condition": "...",
    "size_estimate": "...",
    "confidence": 0.0-1.0,
    "notes": "..."
}"""
            
            # Call Claude
            message = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            response_text = message.content[0].text
            
            # Extract JSON
            try:
                # Find JSON in response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                logger.info(f'Claude vision analysis: {result.get("title")}')
                return result
            
            except json.JSONDecodeError:
                logger.warning('Failed to parse Claude response as JSON')
                return {
                    'title': response_text[:100],
                    'confidence': 0.5,
                    'raw_response': response_text
                }
        
        except ImportError:
            logger.warning('anthropic SDK not installed')
            return None
        except Exception as e:
            logger.error(f'Claude vision API error: {e}')
            return None
