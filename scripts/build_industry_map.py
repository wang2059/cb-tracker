"""
一次性執行：爬 Goodinfo 建立可轉債產業對照表
結果存到 data/industry_map.json，格式：
  { "股票代號": { "industry": "半導體業", "chain": "上游" }, ... }
"""
import sys, io, os, json, csv, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import date, timedelta

# ── 供應鏈位置對應表 ────────────────────────────────
CHAIN_MAP = {
    '半導體業':           '上游',
    '電子零組件業':       '中游',
    '光電業':             '中游',
    '通信網路業':         '中游',
    '電腦及週邊設備業':   '下游',
    '其他電子業':         '中游',
    '電機機械業':         '中游',
    '資訊服務業':         '下游',
    '化學工業':           '上游',
    '化學生技醫療業':     '中游',
    '生技醫療業':         '下游',
    '食品工業':           '下游',
    '紡織纖維業':         '中游',
    '鋼鐵工業':           '上游',
    '塑膠工業':           '中游',
    '橡膠工業':           '中游',
    '汽車工業':           '下游',
    '水泥工業':           '上游',
    '造紙工業':           '中游',
    '玻璃陶瓷業':         '中游',
    '建材營造業':         '下游',
    '航運業':             '下游',
    '觀光餐旅業':         '下游',
    '金融保險業':         '下游',
    '貿易百貨業':         '下游',
    '油電燃氣業':         '上游',
    '文化創意業':         '下游',
    '農業科技業':         '中游',
    '電子商務業':         '下游',
    '存託憑證':           '下游',
    '其他業':             '中游',
    '綜合業':             '下游',
}

def get_chain(industry):
    for key, val in CHAIN_MAP.items():
        if key in industry:
            return val
    return '中游'  # 預設

# ── 取得今日 CB 清單，提取母股代號 ────────────────────
def fetch_stock_ids():
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.tpex.org.tw/'}
    for days_back in range(0, 7):
        d = date.today() - timedelta(days=days_back)
        if d.weekday() >= 5:
            continue
        y, ym, ymd = d.strftime('%Y'), d.strftime('%Y%m'), d.strftime('%Y%m%d')
        url = f'https://www.tpex.org.tw/storage/bond_zone/tradeinfo/cb/{y}/{ym}/RSta0113.{ymd}-C.csv'
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 500:
            text = r.content.decode('big5', errors='replace')
            stock_ids = set()
            for line in text.split('\n'):
                if not line.startswith('BODY'):
                    continue
                try:
                    cols = next(csv.reader([line[5:]]))
                except Exception:
                    continue
                bond_id = cols[0].strip() if cols else ''
                trade   = cols[2].strip() if len(cols) > 2 else ''
                if bond_id and trade == '等價':
                    stock_id = bond_id[:4]  # 前四碼 = 母股代號
                    stock_ids.add(stock_id)
            print(f'取得 {len(stock_ids)} 支母股代號（資料日期 {d}）')
            return sorted(stock_ids)
    return []

# ── Goodinfo 爬蟲 ──────────────────────────────────
def scrape_goodinfo(stock_ids, output_path):
    existing = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f'載入已有資料 {len(existing)} 筆，只爬缺少的')

    to_scrape = [s for s in stock_ids if s not in existing]
    print(f'需要爬取 {len(to_scrape)} 筆')

    if not to_scrape:
        print('全部已有，不需重新爬取')
        return existing

    result = dict(existing)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        )

        # 初始化 Goodinfo session
        init = context.new_page()
        init.goto('https://goodinfo.tw/tw/index.asp', wait_until='domcontentloaded', timeout=20000)
        time.sleep(2)
        init.close()

        for i, stock_id in enumerate(to_scrape):
            pg = context.new_page()
            try:
                url = f'https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}'
                pg.goto(url, wait_until='domcontentloaded', timeout=15000)
                time.sleep(1.5)

                html = pg.content()
                soup = BeautifulSoup(html, 'lxml')

                # 找 產業別
                industry = ''
                for th in soup.find_all('th'):
                    if '產業別' in th.get_text():
                        td = th.find_next_sibling('td')
                        if td:
                            industry = td.get_text(strip=True)
                            break

                if not industry:
                    # regex 備用
                    m = re.search(r'產業別.*?<td[^>]*>\s*(?:<[^>]+>)?([^<\n]{2,20})', html)
                    if m:
                        industry = m.group(1).strip()

                chain = get_chain(industry)
                result[stock_id] = {'industry': industry, 'chain': chain}

                print(f'[{i+1}/{len(to_scrape)}] {stock_id}: {industry} → {chain}')

                # 每 10 筆存一次，避免中斷損失進度
                if (i + 1) % 10 == 0:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f'  → 已存 {len(result)} 筆')

            except Exception as e:
                print(f'[{i+1}/{len(to_scrape)}] {stock_id} 失敗: {e}')
                result[stock_id] = {'industry': '', 'chain': ''}
            finally:
                pg.close()

            time.sleep(1.8)  # rate limit：每筆等 1.8 秒

        browser.close()

    # 最終存檔
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'\n完成！共 {len(result)} 筆存至 {output_path}')
    return result

# ── 主程式 ─────────────────────────────────────────
if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), '..', 'data', 'industry_map.json')
    stock_ids = fetch_stock_ids()
    if stock_ids:
        scrape_goodinfo(stock_ids, out)
    else:
        print('錯誤：無法取得 CB 清單')
