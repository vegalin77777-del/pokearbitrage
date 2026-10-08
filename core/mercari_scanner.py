import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from mercapi import Mercapi

logger = logging.getLogger(__name__)

class MercariScanner:
    def __init__(self):
        pass

    async def _async_search(self, keyword: str, limit: int = 15) -> List[Dict[str, Any]]:
        results = []
        try:
            client = Mercapi()
            response = await client.search(keyword)
            items = getattr(response, 'items', [])
            
            for item in items[:limit]:
                status = getattr(item, 'status', '')
                if 'SOLD' in str(status).upper():
                    continue

                item_id = getattr(item, 'id_', '')
                title = getattr(item, 'name', '')
                price = getattr(item, 'price', 0)
                thumbnails = getattr(item, 'thumbnails', [])
                img_url = thumbnails[0] if thumbnails else ''
                seller_id = getattr(item, 'seller_id', '')

                results.append({
                    'id': item_id,
                    'title': title,
                    'price_jpy': price,
                    'image_url': img_url,
                    'seller_id': seller_id,
                    'seller_name': 'Mercari 賣家',
                    'seller_rating': '評價良好',
                    'platform': 'Mercari',
                    'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            logger.error(f"Mercari search error for '{keyword}': {e}")
        return results

    def run_sync_search(self, keyword: str, limit: int = 15) -> List[Dict[str, Any]]:
        return asyncio.run(self._async_search(keyword, limit=limit))
