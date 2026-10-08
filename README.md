# PokeArbitrage Pro (寶可夢神卡比價雷達與撿漏獵手)

全自動寶可夢 TCG 珍貴卡牌跨平台（Mercari、Cardmarket、eBay）比價、低價賣家獵手與即時一鍵直達下單系統。

## 🌟 核心功能
- **四大保值板塊深度百科**：噴火龍（市值藍籌）、皮卡丘（文化頂峰）、月亮伊布（異畫聖杯）、女性訓練家（Waifu Tax 溢價）。
- **撿漏雷達 (Deal Finder)**：自動偵測便宜 15%~40% 以上的賣家，標註折價率與防偽過濾。
- **跨平台比價矩陣**：歐洲 Cardmarket、美國 eBay、日本/台灣 Mercari 行情對比與圖表。
- **一鍵即時下單**：台灣 Mercari (tw.mercari.com)、日本 Mercari (jp.mercari.com)、Buyee 代購一鍵直通。
- **定期定時背景自動掃描**：支援背景巡檢與 Discord/Telegram 即時推播。

## 🚀 本地快速啟動
```bash
pip install -r requirements.txt
python app.py
```
訪問 http://127.0.0.1:5500

## ☁️ 雲端免費部署 (Render / Railway / Zeabur)
1. Fork 或上傳此專案至 GitHub
2. 在 [Render.com](https://render.com) 選擇 "New Web Service" 並綁定本專案
3. Render 會自動讀取 `render.yaml` 進行雲端部署，完成後即可獲取專屬的公開 HTTPS 網址！
