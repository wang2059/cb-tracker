import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php',
    'Accept': 'application/json, */*',
    'X-Requested-With': 'XMLHttpRequest',
}

# 找 tables.js 的 apiOption 邏輯
js = requests.get('https://www.tpex.org.tw/rsrc/js/tables.js', headers=headers, timeout=10).text
idx = js.find('apiOption')
print("apiOption 附近：")
print(js[max(0,idx-100):idx+300])
print()

# 試 option 端點
option_urls = [
    'https://www.tpex.org.tw/www/zh-tw/bond/cbDaily/option',
    'https://www.tpex.org.tw/www/zh-tw/bond/option',
    'https://www.tpex.org.tw/www/zh-tw/api/option',
]

for url in option_urls:
    try:
        r = requests.get(url, params={'name': 'fileCode'}, headers=headers, timeout=8)
        print(f"GET {url.split('/')[-2]}/{url.split('/')[-1]}?name=fileCode")
        print(f"  => {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(f"  FAIL: {e}")

# 也試不同的 bond action 名稱
print("\n試其他可能的 action：")
actions = ['cbPrice', 'cbprice', 'cb/price', 'cbMarket', 'cbQuote', 'bond/cb']
for action in actions:
    url = f'https://www.tpex.org.tw/www/zh-tw/{action}'
    try:
        r = requests.post(url, data={}, headers=headers, timeout=5)
        print(f"  POST /www/zh-tw/{action} => {r.status_code} | {r.text[:100]}")
    except Exception as e:
        print(f"  POST /www/zh-tw/{action} => FAIL: {e}")
