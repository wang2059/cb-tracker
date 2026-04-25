import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
from datetime import date, timedelta

d = date.today() - timedelta(days=1)
roc = f'{d.year-1911}/{d.month:02d}/{d.day:02d}'

api_responses = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 攔截所有 API 回應
    def handle_response(response):
        url = response.url
        if 'www/zh-tw' in url and response.status == 200:
            try:
                ct = response.headers.get('content-type', '')
                if 'json' in ct:
                    body = response.json()
                    api_responses.append({'url': url, 'data': body})
                    print(f"[攔截到 JSON] {url}")
                    print(f"  stat={body.get('stat')}, keys={list(body.keys())}")
            except Exception:
                pass

    page.on('response', handle_response)

    print(f"開啟 TPEX CB Daily 頁面（日期 {roc}）...")
    page.goto(f'https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php?l=zh-tw&d={roc}',
              wait_until='networkidle', timeout=30000)

    print("\n等待資料載入...")
    page.wait_for_timeout(3000)

    # 印出頁面標題
    title = page.title()
    print(f"頁面標題: {title}")

    # 找頁面上所有 table
    tables = page.query_selector_all('table')
    print(f"找到 {len(tables)} 個 table")

    # 找所有可轉債相關文字
    content = page.inner_text('body')
    lines = [l.strip() for l in content.split('\n') if l.strip() and len(l.strip()) > 3]
    print(f"\n頁面文字（前 30 行）：")
    for line in lines[:30]:
        print(f"  {line}")

    browser.close()

print(f"\n\n共攔截到 {len(api_responses)} 個 JSON API 回應")
for resp in api_responses:
    print(f"\nURL: {resp['url']}")
    print(json.dumps(resp['data'], ensure_ascii=False, indent=2)[:500])
