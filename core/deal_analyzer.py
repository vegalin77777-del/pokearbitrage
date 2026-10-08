import re
from typing import Dict, Any, List

class DealAnalyzer:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.anti_scam_keywords = settings.get('anti_scam_keywords', [
            '複製', '複製品', '展示品', '非公式', '同人', 'proxy', 'replica',
            'ジャンク', 'junk', 'オリパ', 'mystery', '空箱', 'boxのみ', 'ノーマルのみ', 'おまけ'
        ])
        self.super_deal_threshold = settings.get('deal_thresholds', {}).get('super_deal_pct', 30.0)
        self.good_deal_threshold = settings.get('deal_thresholds', {}).get('good_deal_pct', 15.0)
        self.jpy_rate = settings.get('exchange_rates', {}).get('JPY_TO_TWD', 0.212)
        self.usd_rate = settings.get('exchange_rates', {}).get('USD_TO_TWD', 32.2)

    def check_suspicious(self, title: str, description: str = '') -> tuple[bool, str]:
        text = (title + ' ' + description).lower()
        for kw in self.anti_scam_keywords:
            if kw.lower() in text:
                return True, f'偵測到可疑關鍵字: 【{kw}】(疑似複製品/空箱/福袋/展示品)'
        return False, ''

    def detect_grade(self, title: str) -> str:
        text = title.upper()
        if 'PSA 10' in text or 'PSA10' in text:
            return 'PSA 10'
        elif 'PSA 9' in text or 'PSA9' in text:
            return 'PSA 9'
        elif 'BGS 10' in text or 'BGS10' in text:
            return 'BGS 10'
        elif 'BGS 9.5' in text or 'BGS9.5' in text:
            return 'BGS 9.5'
        elif 'CGC 10' in text:
            return 'CGC 10'
        elif 'PSA' in text:
            return 'PSA 鑑定卡'
        elif '未開封' in text or 'SEALED' in text:
            return '未開封/全新品'
        elif '美品' in text or 'NM' in text:
            return '美品 (Near Mint)'
        return '裸卡 / 原卡'

    def analyze_deal(self, item: Dict[str, Any], card_info: Dict[str, Any]) -> Dict[str, Any]:
        item_id = item.get('id', '')
        title = item.get('title', '')
        price_jpy = float(item.get('price_jpy', 0))
        price_twd = round(price_jpy * self.jpy_rate)
        
        grade = self.detect_grade(title)
        fair_price_jpy = float(card_info.get('market_fair_value_jpy', 0))
        fair_price_twd = float(card_info.get('market_fair_value_twd', 0))
        
        # 依鑑定等級評估行情基準
        if 'PSA 10' in grade or 'BGS 10' in grade:
            fair_price_jpy = fair_price_jpy * 3.5
            fair_price_twd = fair_price_twd * 3.5
        elif 'PSA 9' in grade:
            fair_price_jpy = fair_price_jpy * 1.5
            fair_price_twd = fair_price_twd * 1.5

        if fair_price_jpy > 0:
            discount_pct = round(((fair_price_jpy - price_jpy) / fair_price_jpy) * 100, 1)
        else:
            discount_pct = 0.0

        savings_twd = round(fair_price_twd - price_twd)

        is_suspicious, scam_reason = self.check_suspicious(title)
        
        if discount_pct > 85.0 and not is_suspicious:
            is_suspicious = True
            scam_reason = '價格異常偏低 (>85% 折扣)，請高度警惕假卡或瑕疵'

        if is_suspicious:
            deal_tier = 'SUSPICIOUS'
            tier_label = '⚠️ 警示/疑似假卡'
            tier_badge = 'border-rose-500 bg-rose-950/40 text-rose-300'
        elif discount_pct >= self.super_deal_threshold:
            deal_tier = 'SUPER_DEAL'
            tier_label = '🔥 神價撿漏'
            tier_badge = 'border-emerald-500 bg-emerald-950/40 text-emerald-300'
        elif discount_pct >= self.good_deal_threshold:
            deal_tier = 'GOOD_DEAL'
            tier_label = '⭐ 超值好價'
            tier_badge = 'border-cyan-500 bg-cyan-950/40 text-cyan-300'
        elif discount_pct >= -15.0:
            deal_tier = 'FAIR_PRICE'
            tier_label = '⚖️ 公道行情'
            tier_badge = 'border-slate-600 bg-slate-800 text-slate-300'
        else:
            deal_tier = 'OVERPRICED'
            tier_label = '📈 偏高行情'
            tier_badge = 'border-amber-600 bg-amber-950/40 text-amber-300'

        cm_slug = card_info.get('cardmarket_slug', '')
        links = {
            'tw_mercari': f'https://tw.mercari.com/zh-hant/item/{item_id}',
            'jp_mercari': f'https://jp.mercari.com/item/{item_id}',
            'buyee': f'https://buyee.jp/mercari/item/{item_id}?conversionType=service_page_search',
            'cardmarket': f'https://www.cardmarket.com/en/Pokemon/Products/Singles/{cm_slug}' if cm_slug else 'https://www.cardmarket.com/en/Pokemon'
        }

        return {
            'item_id': item_id,
            'card_id': card_info.get('id'),
            'card_name_zh': card_info.get('name_zh'),
            'card_name_ja': card_info.get('name_ja'),
            'category': card_info.get('category'),
            'title': title,
            'image_url': item.get('image_url') or card_info.get('image_url'),
            'price_jpy': price_jpy,
            'price_twd': price_twd,
            'fair_price_jpy': round(fair_price_jpy),
            'fair_price_twd': round(fair_price_twd),
            'savings_twd': savings_twd,
            'discount_pct': discount_pct,
            'grade': grade,
            'deal_tier': deal_tier,
            'tier_label': tier_label,
            'tier_badge': tier_badge,
            'is_suspicious': is_suspicious,
            'scam_reason': scam_reason,
            'seller_id': item.get('seller_id', ''),
            'seller_name': item.get('seller_name', 'Mercari 賣家'),
            'seller_rating': item.get('seller_rating', '安心賣家'),
            'links': links,
            'scanned_at': item.get('scanned_at', '')
        }
