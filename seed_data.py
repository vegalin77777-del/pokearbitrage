import json
import random
from datetime import datetime
from core.deal_analyzer import DealAnalyzer
import config

with open(config.CARDS_DB_PATH, 'r', encoding='utf-8') as f:
    cards = json.load(f)

analyzer = DealAnalyzer(config.DEFAULT_SETTINGS)

sample_deals = []

# 為前 10 張核心保值卡牌建立真實賣家範例資料 (涵蓋神價、好價、正常價與鑑定卡)
sample_sellers = [
    ('ポケカ専門ショップ☆即購入OK', '安心高評價賣家'),
    ('コレクション整理中@迅速発送', '個人收藏家 (99.8%好評)'),
    ('TCGトレカ堂@スリーブローダー付', '優質店鋪'),
    ('メルカリ古参★24時間以内発送', '金牌賣家'),
    ('引退品まとめ処分', '急售賣家')
]

for card in cards[:12]:
    base_price = card['market_fair_value_jpy']
    
    # 賣家 1: 神價撿漏 (比市價便宜 22%~38%)
    p1 = round(base_price * random.uniform(0.62, 0.78), -2)
    t1 = f【美品】{card['name_ja']} ローダー付き 即購入可
    deal1 = analyzer.analyze_deal({
        'id': fm{random.randint(10000000000, 99999999999)},
        'title': t1,
        'price_jpy': p1,
        'image_url': card['image_url'],
        'seller_id': fu{random.randint(10000000, 99999999)},
        'seller_name': sample_sellers[0][0],
        'seller_rating': sample_sellers[0][1],
        'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, card)
    sample_deals.append(deal1)

    # 賣家 2: PSA 10 鑑定卡 (好價或市價)
    p2 = round(base_price * 3.5 * random.uniform(0.75, 0.92), -2)
    t2 = f【PSA10 最高評価】{card['name_ja']} 鑑定品 ワンオーナー
    deal2 = analyzer.analyze_deal({
        'id': fm{random.randint(10000000000, 99999999999)},
        'title': t2,
        'price_jpy': p2,
        'image_url': card['image_url'],
        'seller_id': fu{random.randint(10000000, 99999999)},
        'seller_name': sample_sellers[1][0],
        'seller_rating': sample_sellers[1][1],
        'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, card)
    sample_deals.append(deal2)

    # 賣家 3: 公道市價
    p3 = round(base_price * random.uniform(0.95, 1.05), -2)
    t3 = f{card['name_ja']} 白かけなし 横線なし
    deal3 = analyzer.analyze_deal({
        'id': fm{random.randint(10000000000, 99999999999)},
        'title': t3,
        'price_jpy': p3,
        'image_url': card['image_url'],
        'seller_id': fu{random.randint(10000000, 99999999)},
        'seller_name': sample_sellers[2][0],
        'seller_rating': sample_sellers[2][1],
        'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, card)
    sample_deals.append(deal3)

# 依折扣率排序
sample_deals.sort(key=lambda d: d.get('discount_pct', 0), reverse=True)

with open(config.SCAN_HISTORY_PATH, 'w', encoding='utf-8') as f:
    json.dump({
        'last_scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_deals': len(sample_deals),
        'deals': sample_deals
    }, f, ensure_ascii=False, indent=2)

print(fSeeded {len(sample_deals)} initial deals to scan_history.json)
