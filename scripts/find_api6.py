import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json
from datetime import date, timedelta

d = date.today() - timedelta(days=1)
roc_year  = str(d.year - 1911)          # 115
roc_month = f'{d.month:02d}'            # 04
roc_ym    = roc_year + roc_month        # 11504
roc_full  = f'{roc_year}/{roc_month}/{d.day:02d}'  # 115/04/24

# 更完整的瀏覽器 header
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.tpex.org.tw',
    'Referer': 'https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php?l=zh-tw',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'X-Requested-With': 'XMLHttpRequest',
}

url = 'https://www.tpex.org.tw/www/zh-tw/bond/cbDaily'
option_url = 'https://www.tpex.org.tw/www/zh-tw/bond/cbDaily/option'

# 試 option 端點（GET + POST）
print("=== option 端點 ===")
for method, params in [
    ('GET', {'name': 'fileCode'}),
    ('POST', {'name': 'fileCode'}),
    ('GET', {'name': 'fileCode', 'l': 'zh-tw'}),
]:
    r = getattr(requests, method.lower())(option_url, params=params if method=='GET' else None,
        data=params if method=='POST' else None, headers=headers, timeout=8)
    try:
        print(f"{method} option {params} => {r.json()}")
    except Exception:
        print(f"{method} option {params} => {r.text[:80]}")

# 試 cbDaily POST 含月份代碼
print("\n=== cbDaily POST 月份代碼 ===")
combos = [
    {'fileCode': roc_ym},              # 11504
    {'fileCode': roc_year},            # 115
    {'fileCode': roc_ym, 'l': 'zh-tw'},
    {'fileCode': 'CB', 'd': roc_full},
    {'fileCode': roc_ym, 'd': roc_full},
    {'year': roc_year, 'month': roc_month},
    {'ym': roc_ym},
]
for params in combos:
    r = requests.post(url, data=params, headers=headers, timeout=8)
    try:
        result = r.json()
        stat = result.get('stat', '?')
        print(f"  {params} => {stat}")
        if stat == 'ok':
            print("  *** 成功！", json.dumps(result, ensure_ascii=False)[:400])
    except Exception:
        print(f"  {params} => 非JSON {r.text[:60]}")
