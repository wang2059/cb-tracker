import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json, re
from datetime import date, timedelta

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-TW,zh;q=0.9',
})

d = date.today() - timedelta(days=1)
roc = f'{d.year-1911}/{d.month:02d}/{d.day:02d}'

# 步驟 1：先訪問頁面取得 cookie
page_url = f'https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php?l=zh-tw&d={roc}'
r0 = session.get(page_url, timeout=15)
print(f"頁面狀態: {r0.status_code}")
print(f"Cookie: {dict(session.cookies)}")

# 步驟 2：找頁面中任何 hidden input 或 token
html = r0.content.decode('utf-8', errors='replace')
tokens = re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.IGNORECASE)
print(f"\nHidden inputs: {tokens[:5]}")

# 步驟 3：POST
post_headers = {
    'Referer': page_url,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.tpex.org.tw',
}

url = 'https://www.tpex.org.tw/www/zh-tw/bond/cbDaily'
combos = [
    {'l': 'zh-tw', 'd': roc},
    {'d': roc},
    {'l': 'zh-tw'},
    {'l': 'zh-tw', 'd': roc, 'o': 'json'},
]

print()
for params in combos:
    r = session.post(url, data=params, headers=post_headers, timeout=10)
    try:
        result = r.json()
        stat = result.get('stat', '?')
        print(f"  {params} => stat={stat}, keys={list(result.keys())}")
        if stat == 'ok':
            print("  *** 成功！", json.dumps(result, ensure_ascii=False)[:300])
    except Exception:
        print(f"  {params} => 非JSON: {r.text[:100]}")
