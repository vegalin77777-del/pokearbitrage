import os

# 基礎路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
CARDS_DB_PATH = os.path.join(DB_DIR, 'cards_db.json')
SCAN_HISTORY_PATH = os.path.join(DB_DIR, 'scan_history.json')
SETTINGS_PATH = os.path.join(DB_DIR, 'settings.json')

# 匯率換算設定 (可透過 UI 動態調整)
DEFAULT_SETTINGS = {
    'exchange_rates': {
        'JPY_TO_TWD': 0.212,   # 1 日圓換算新台幣
        'USD_TO_TWD': 32.2,    # 1 美元換算新台幣
        'EUR_TO_TWD': 35.0     # 1 歐元換算新台幣
    },
    'scan_interval_minutes': 30, # 自動掃描間隔 (分鐘)
    'auto_scan_enabled': True,
    'deal_thresholds': {
        'super_deal_pct': 30.0, # 便宜超過 30% 列為神價
        'good_deal_pct': 15.0   # 便宜超過 15% 列為超值
    },
    'preferred_platform': 'tw_mercari', # 預設下單跳轉: 'tw_mercari', 'jp_mercari', 'buyee'
    'anti_scam_keywords': [
        '複製', '複製品', '展示品', '非公式', '同人', 'proxy', 'replica',
        'ジャンク', 'junk', 'オリパ', 'mystery', '空箱', 'boxのみ', 'ノーマルのみ'
    ],
    'notifications': {
        'discord_webhook_url': '',
        'telegram_bot_token': '',
        'telegram_chat_id': '',
        'line_notify_token': '',
        'notify_on_super_deal_only': False
    }
}
