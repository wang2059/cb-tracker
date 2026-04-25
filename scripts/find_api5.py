import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json, re
from datetime import date, timedelta

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tpex.org.tw/',
    'Accept': 'application/json, */*',
    'X-Requested-With': 'XMLHttpRequest',
}

# 掃 main.js 找所有 action: 字串
js = requests.get('https://www.tpex.org.tw/rsrc/js/main.js', headers=headers, timeout=10).text
actions = re.findall(r'action\s*:\s*["\']([^"\']+)["\']', js)
print("main.js 所有 action：")
for a in sorted(set(actions)):
    print(f"  {a}")

# 重點找 bond 開頭的
bond_actions = [a for a in actions if 'bond' in a.lower() or 'cb' in a.lower()]
print(f"\nbond/cb 相關：{bond_actions}")

# 試這些 action 的 POST
d = date.today() - timedelta(days=1)
roc = f'{d.year-1911}/{d.month:02d}/{d.day:02d}'
print(f"\n試各 bond action POST（日期 {roc}）：")
for action in bond_actions:
    url = f'https://www.tpex.org.tw/www/zh-tw/{action}'
    try:
        r = requests.post(url, data={'d': roc}, headers=headers, timeout=5)
        try:
            stat = r.json().get('stat', '?')
        except Exception:
            stat = r.text[:60]
        print(f"  {action} => {stat}")
    except Exception as e:
        print(f"  {action} => FAIL")
