import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request

import config
from core.scheduler import ScanManager
from core.cardmarket_scanner import CardmarketScanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 初始化掃描管理器與比價引擎
scan_manager = ScanManager(config)
cardmarket_scanner = CardmarketScanner(scan_manager.settings)

# 啟動背景定期定時掃描排程器
scan_manager.start_background_scheduler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cards', methods=['GET'])
def get_cards():
    """取得所有保值珍貴卡牌庫列表與詳細資訊"""
    category = request.args.get('category', 'all')
    cards = scan_manager.cards
    if category != 'all':
        cards = [c for c in cards if c.get('category') == category]
    return jsonify({
        'status': 'success',
        'total': len(cards),
        'cards': cards
    })

@app.route('/api/cards/<card_id>', methods=['GET'])
def get_card_detail(card_id):
    """取得單張卡牌詳細資訊與跨平台比價數據"""
    card = next((c for c in scan_manager.cards if c['id'] == card_id), None)
    if not card:
        return jsonify({'status': 'error', 'message': 'Card not found'}), 404

    benchmark = cardmarket_scanner.get_benchmark_prices(card)
    card_deals = [d for d in scan_manager.latest_deals if d.get('card_id') == card_id]

    return jsonify({
        'status': 'success',
        'card': card,
        'benchmark': benchmark,
        'deals': card_deals
    })

@app.route('/api/deals', methods=['GET'])
def get_deals():
    """取得當前撿漏雷達與賣家商品清單 (支援多維度篩選排序)"""
    category = request.args.get('category', 'all')
    tier = request.args.get('tier', 'all')
    exclude_suspicious = request.args.get('exclude_suspicious', 'true').lower() == 'true'
    sort_by = request.args.get('sort', 'discount') # discount, price_asc, savings_desc

    deals = list(scan_manager.latest_deals)

    if category != 'all':
        deals = [d for d in deals if d.get('category') == category]

    if tier != 'all':
        deals = [d for d in deals if d.get('deal_tier') == tier]

    if exclude_suspicious:
        deals = [d for d in deals if not d.get('is_suspicious', False)]

    # 排序
    if sort_by == 'discount':
        deals.sort(key=lambda x: x.get('discount_pct', 0), reverse=True)
    elif sort_by == 'price_asc':
        deals.sort(key=lambda x: x.get('price_twd', 0))
    elif sort_by == 'savings_desc':
        deals.sort(key=lambda x: x.get('savings_twd', 0), reverse=True)

    # 統計指標
    total_super = sum(1 for d in scan_manager.latest_deals if d.get('deal_tier') == 'SUPER_DEAL')
    total_good = sum(1 for d in scan_manager.latest_deals if d.get('deal_tier') == 'GOOD_DEAL')
    avg_discount = round(sum(d.get('discount_pct', 0) for d in deals) / max(1, len(deals)), 1) if deals else 0

    return jsonify({
        'status': 'success',
        'total': len(deals),
        'metrics': {
            'super_deals': total_super,
            'good_deals': total_good,
            'avg_discount': avg_discount,
            'last_scan_time': scan_manager.last_scan_time or '未掃描'
        },
        'deals': deals
    })

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """手動觸發即時掃描 (支援全庫掃描或特定卡牌掃描)"""
    data = request.get_json() or {}
    target_card_id = data.get('card_id')

    if scan_manager.is_scanning:
        return jsonify({
            'status': 'busy',
            'message': '系統正在執行掃描中，請稍候...',
            'progress': scan_manager.scan_progress
        })

    import threading
    thread = threading.Thread(target=scan_manager.perform_scan, args=(target_card_id,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'started',
        'message': f'已啟動{"【全庫】" if not target_card_id else "【指定卡牌】"}掃描任務！'
    })

@app.route('/api/scan/status', methods=['GET'])
def get_scan_status():
    """取得即時掃描進度與狀態"""
    total = scan_manager.scan_progress.get('total', 0)
    current = scan_manager.scan_progress.get('current', 0)
    pct = round((current / total * 100), 1) if total > 0 else 0

    return jsonify({
        'is_scanning': scan_manager.is_scanning,
        'current': current,
        'total': total,
        'percentage': pct,
        'current_card': scan_manager.scan_progress.get('current_card', ''),
        'last_scan_time': scan_manager.last_scan_time
    })

@app.route('/api/comparison', methods=['GET'])
def get_comparison_matrix():
    """取得跨平台 (Mercari vs Cardmarket vs eBay vs PSA10) 橫向比價矩陣"""
    matrix = []
    for card in scan_manager.cards:
        benchmarks = cardmarket_scanner.get_benchmark_prices(card)
        
        # 尋找 Mercari 當前最低價
        card_deals = [d for d in scan_manager.latest_deals if d.get('card_id') == card['id'] and not d.get('is_suspicious')]
        min_deal_twd = min([d['price_twd'] for d in card_deals]) if card_deals else card['market_fair_value_twd']
        best_deal = min(card_deals, key=lambda x: x['price_twd']) if card_deals else None

        matrix.append({
            'card_id': card['id'],
            'name_zh': card['name_zh'],
            'category_name': card['category_name'],
            'release_year': card['release_year'],
            'image_url': card['image_url'],
            'fair_price_twd': card['market_fair_value_twd'],
            'mercari_min_twd': min_deal_twd,
            'cardmarket_trend_twd': benchmarks['cardmarket']['trend_price_twd'],
            'cardmarket_min_twd': benchmarks['cardmarket']['min_price_twd'],
            'ebay_sold_twd': benchmarks['ebay']['avg_sold_price_twd'],
            'psa10_market_usd': card.get('psa10_market_usd', ''),
            'psa10_record_usd': card.get('psa10_record_usd', 0),
            'best_deal': best_deal,
            'cardmarket_url': benchmarks['cardmarket']['url']
        })

    return jsonify({
        'status': 'success',
        'total': len(matrix),
        'comparison': matrix
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    """管理系統設定 (匯率、排程間隔、通知 Webhook、預設下單跳轉平台)"""
    if request.method == 'POST':
        new_settings = request.get_json() or {}
        scan_manager.save_settings(new_settings)
        # 同步更新 Cardmarket 比價引擎匯率
        global cardmarket_scanner
        cardmarket_scanner = CardmarketScanner(scan_manager.settings)
        return jsonify({'status': 'success', 'message': '設定已成功儲存！', 'settings': scan_manager.settings})

    return jsonify({
        'status': 'success',
        'settings': scan_manager.settings
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5500))
    logger.info(f"🚀 PokeArbitrage Pro 啟動於 http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
