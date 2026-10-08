import json
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.notif_config = settings.get('notifications', {})

    def send_deal_alert(self, deal: Dict[str, Any]) -> bool:
        title = deal.get('title', '未知卡牌')
        card_name = deal.get('card_name_zh', '')
        discount = deal.get('discount_pct', 0)
        price_twd = deal.get('price_twd', 0)
        fair_price_twd = deal.get('fair_price_twd', 0)
        savings_twd = deal.get('savings_twd', 0)
        buy_url = deal.get('links', {}).get('tw_mercari', '')
        grade = deal.get('grade', '裸卡')

        discord_url = self.notif_config.get('discord_webhook_url')
        if discord_url:
            try:
                payload = {
                    'username': 'PokeArbitrage 雷達獵手',
                    'embeds': [{
                        'title': f'🔥 發現撿漏標的！【{card_name}】省下 NT$ {savings_twd:,}',
                        'description': f'**賣家標題**：{title}\n**狀態品項**：`{grade}`\n**折扣幅度**：**{discount}% OFF**',
                        'color': 0x10B981 if discount >= 30 else 0x06B6D4,
                        'fields': [
                            {'name': '特價金額', 'value': f'NT$ {price_twd:,}', 'inline': True},
                            {'name': '行情基準', 'value': f'NT$ {fair_price_twd:,}', 'inline': True},
                            {'name': '現省金額', 'value': f'NT$ {savings_twd:,}', 'inline': True}
                        ],
                        'url': buy_url,
                        'thumbnail': {'url': deal.get('image_url', '')}
                    }]
                }
                requests.post(discord_url, json=payload, timeout=5)
            except Exception as e:
                logger.error(f'Discord webhook error: {e}')
        return True
