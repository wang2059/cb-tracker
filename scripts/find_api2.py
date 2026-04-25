import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json
from datetime import date, timedelta

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php',
    'Accept': 'application/json, */*',
    'X-Requested-With': 'XMLHttpRequest',
}

url = 'https://www.tpex.org.tw/www/zh-tw/bond/cbDaily'
d = date.today() - timedelta(days=1)
roc = f'{d.year-1911}/{d.month:02d}/{d.day:02d}'

# 頁面 URL 是 CBDaily.php?l=zh-tw，所以 o = {l: 'zh-tw'}
# 或是 CBDaily.php（空），然後 autoLoad 觸發
combos = [
    {},                                  # 空
    {'l': 'zh-tw'},                      # 只有語言
    {'l': 'zh-tw', 'd': roc},            # 語言 + 日期
    {'fileCode': str(d.year - 1911)},    # 年份（民國）
    {'fileCode': 'all'},
    {'fileCode': roc[:3]},               # 115
]

for params in combos:
    r = requests.post(url, data=params, headers=headers, timeout=10)
    try:
        result = r.json()
        stat = result.get('stat', '?')
        keys = list(result.keys())
        print(f"POST {params} => stat={stat}, keys={keys}")
        if stat == 'ok':
            print("  *** 成功！完整回應：")
            print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
    except Exception:
        print(f"POST {params} => 非 JSON: {r.text[:80]}")
