import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, re
from datetime import date, timedelta

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# 找 tables.js 裡 POST 前的參數組合邏輯
js = requests.get('https://www.tpex.org.tw/rsrc/js/tables.js', headers=headers, timeout=10).text
idx = js.rfind('$.post')
print("POST 呼叫前 800 字：")
print(js[max(0, idx-600):idx+200])
print()

# 同時試各種參數組合
d = date.today() - timedelta(days=1)
roc = f'{d.year-1911}/{d.month:02d}/{d.day:02d}'
url = 'https://www.tpex.org.tw/www/zh-tw/bond/cbDaily'

print(f"\n試各種 POST 參數（日期 {roc}）：")
combos = [
    {'d': roc, 'fileCode': 'CB'},
    {'d': roc, 'fileCode': ''},
    {'d': roc, 'l': 'zh-tw'},
    {'inputDate': roc},
    {'queryDate': roc},
    {'d': roc, 'type': 'CB'},
    {'inpuYear': str(d.year-1911), 'inpuMonth': str(d.month), 'inpuDay': str(d.day)},
]

for params in combos:
    r = requests.post(url, data=params, headers=headers, timeout=10)
    stat = r.json().get('stat', '?') if r.headers.get('Content-Type','').startswith('application/json') else r.text[:50]
    print(f"  {params} => {stat}")
