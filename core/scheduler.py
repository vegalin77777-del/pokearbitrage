import json
import time
import os
import threading
import logging
from datetime import datetime
from typing import Dict, Any, List

from core.mercari_scanner import MercariScanner
from core.deal_analyzer import DealAnalyzer
from core.notifier import NotificationManager

logger = logging.getLogger(__name__)

class ScanManager:
    def __init__(self, config_module):
        self.config = config_module
        self.settings = self._load_settings()
        self.cards = self._load_cards()
        self.mercari_scanner = MercariScanner()
        self.deal_analyzer = DealAnalyzer(self.settings)
        self.notifier = NotificationManager(self.settings)
        
        self.is_scanning = False
        self.last_scan_time = None
        self.scan_progress = {'current': 0, 'total': 0, 'current_card': ''}
        self.latest_deals = []
        self._thread = None
        self._stop_event = threading.Event()

        self._load_cached_deals()

    def _load_settings(self) -> Dict[str, Any]:
        if os.path.exists(self.config.SETTINGS_PATH):
            try:
                with open(self.config.SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f'Failed to load settings: {e}')
        return dict(self.config.DEFAULT_SETTINGS)

    def save_settings(self, new_settings: Dict[str, Any]):
        self.settings.update(new_settings)
        self.deal_analyzer = DealAnalyzer(self.settings)
        self.notifier = NotificationManager(self.settings)
        with open(self.config.SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def _load_cards(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.config.CARDS_DB_PATH):
            with open(self.config.CARDS_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _load_cached_deals(self):
        if os.path.exists(self.config.SCAN_HISTORY_PATH):
            try:
                with open(self.config.SCAN_HISTORY_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.latest_deals = data.get('deals', [])
                    self.last_scan_time = data.get('last_scan_time')
            except Exception as e:
                logger.error(f'Error loading scan history: {e}')

    def _save_scan_history(self):
        try:
            with open(self.config.SCAN_HISTORY_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_scan_time': self.last_scan_time,
                    'total_deals': len(self.latest_deals),
                    'deals': self.latest_deals
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'Error saving scan history: {e}')

    def perform_scan(self, target_card_id: str = None) -> List[Dict[str, Any]]:
        if self.is_scanning:
            return self.latest_deals

        self.is_scanning = True
        cards_to_scan = [c for c in self.cards if c['id'] == target_card_id] if target_card_id else self.cards
        self.scan_progress = {'current': 0, 'total': len(cards_to_scan), 'current_card': ''}

        found_deals = []
        try:
            for idx, card in enumerate(cards_to_scan):
                self.scan_progress['current'] = idx + 1
                self.scan_progress['current_card'] = card['name_zh']
                
                keyword = card.get('search_keywords_mercari') or card.get('name_ja')
                items = self.mercari_scanner.run_sync_search(keyword, limit=8)
                
                for item in items:
                    analyzed = self.deal_analyzer.analyze_deal(item, card)
                    found_deals.append(analyzed)
                    
                    if analyzed['deal_tier'] == 'SUPER_DEAL':
                        self.notifier.send_deal_alert(analyzed)
                    elif analyzed['deal_tier'] == 'GOOD_DEAL' and not self.settings.get('notifications', {}).get('notify_on_super_deal_only', False):
                        self.notifier.send_deal_alert(analyzed)

                time.sleep(1.0)

            found_deals.sort(key=lambda d: d.get('discount_pct', 0), reverse=True)
            
            if target_card_id:
                other_deals = [d for d in self.latest_deals if d.get('card_id') != target_card_id]
                self.latest_deals = sorted(other_deals + found_deals, key=lambda d: d.get('discount_pct', 0), reverse=True)
            else:
                if found_deals:
                    self.latest_deals = found_deals

            self.last_scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_scan_history()
        except Exception as e:
            logger.error(f'Scan exception: {e}')
        finally:
            self.is_scanning = False
            self.scan_progress = {'current': 0, 'total': 0, 'current_card': ''}

        return self.latest_deals

    def start_background_scheduler(self):
        def run_loop():
            while not self._stop_event.is_set():
                if self.settings.get('auto_scan_enabled', True):
                    interval_sec = max(60, self.settings.get('scan_interval_minutes', 30) * 60)
                    self.perform_scan()
                    self._stop_event.wait(interval_sec)
                else:
                    self._stop_event.wait(30)

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

    def stop_background_scheduler(self):
        self._stop_event.set()
