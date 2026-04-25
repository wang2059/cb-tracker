import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import re, time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0')

    init = context.new_page()
    init.goto('https://goodinfo.tw/tw/index.asp', wait_until='domcontentloaded', timeout=20000)
    time.sleep(2)
    init.close()

    pg = context.new_page()
    pg.goto('https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=2330',
            wait_until='domcontentloaded', timeout=20000)
    time.sleep(2)

    html = pg.content()
    soup = BeautifulSoup(html, 'lxml')

    # 印出所有 th 欄位名稱
    print('=== 所有 <th> 欄位 ===')
    seen = set()
    for th in soup.find_all('th'):
        txt = th.get_text(strip=True)
        if txt and txt not in seen and len(txt) < 30:
            seen.add(txt)
            td = th.find_next_sibling('td')
            val = td.get_text(strip=True)[:50] if td else ''
            print(f'  [{txt}] = {val}')

    # 找 基本資料 section 的所有 table
    print('\n=== 基本資料區塊 ===')
    for table in soup.find_all('table'):
        text = table.get_text(' ', strip=True)
        if '產業' in text or '主要' in text or '類別' in text:
            rows = table.find_all('tr')
            for row in rows[:10]:
                cells = [c.get_text(strip=True) for c in row.find_all(['td','th'])]
                if any(cells):
                    print(f'  {cells}')
            print()

    pg.close()
    browser.close()
