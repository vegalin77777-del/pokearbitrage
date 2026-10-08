import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CardmarketScanner:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.eur_rate = settings.get('exchange_rates', {}).get('EUR_TO_TWD', 35.0)
        self.usd_rate = settings.get('exchange_rates', {}).get('USD_TO_TWD', 32.2)

    def get_benchmark_prices(self, card_info: Dict[str, Any]) -> Dict[str, Any]:
        fair_usd = float(card_info.get('market_fair_value_usd', 100))
        fair_twd = float(card_info.get('market_fair_value_twd', 3200))
        fair_jpy = float(card_info.get('market_fair_value_jpy', 15000))

        cardmarket_eur = round(fair_usd * 0.92, 1)
        cardmarket_twd = round(cardmarket_eur * self.eur_rate)
        cardmarket_trend_eur = round(cardmarket_eur * 1.08, 1)
        cardmarket_trend_twd = round(cardmarket_trend_eur * self.eur_rate)
        cardmarket_min_eur = round(cardmarket_eur * 0.85, 1)
        cardmarket_min_twd = round(cardmarket_min_eur * self.eur_rate)

        slug = card_info.get('cardmarket_slug', '')
        direct_url = f'https://www.cardmarket.com/en/Pokemon/Products/Singles/{slug}' if slug else 'https://www.cardmarket.com/en/Pokemon'

        return {
            'cardmarket': {
                'currency': 'EUR',
                'min_price': cardmarket_min_eur,
                'min_price_twd': cardmarket_min_twd,
                'trend_price': cardmarket_trend_eur,
                'trend_price_twd': cardmarket_trend_twd,
                'avg_30_days': cardmarket_eur,
                'avg_30_days_twd': cardmarket_twd,
                'url': direct_url
            },
            'tcgplayer': {
                'currency': 'USD',
                'market_price': round(fair_usd, 1),
                'market_price_twd': round(fair_usd * self.usd_rate),
                'url': f"https://www.tcgplayer.com/search/pokemon/product?q={card_info.get('name_en', '').replace(' ', '+')}"
            },
            'ebay': {
                'currency': 'USD',
                'avg_sold_price': round(fair_usd * 1.05, 1),
                'avg_sold_price_twd': round(fair_usd * 1.05 * self.usd_rate),
                'url': f"https://www.ebay.com/sch/i.html?_nkw={card_info.get('name_en', '').replace(' ', '+')}+pokemon+card"
            },
            'mercari_benchmark': {
                'currency': 'JPY',
                'fair_price_jpy': fair_jpy,
                'fair_price_twd': fair_twd
            }
        }
