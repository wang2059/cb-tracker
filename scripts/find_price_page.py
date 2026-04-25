import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://www.tpex.org.tw/'}

# 找 TPEX 所有可轉債相關頁面
# 從 main.js 找所有包含 cb 或 bond 的路由/連結
js = requests.get('https://www.tpex.org.tw/rsrc/js/main.js', headers=headers, timeout=10).text
paths = re.findall(r'["\']([/a-zA-Z0-9_-]*(?:bond|cb|CB|convert)[/a-zA-Z0-9_-]*\.php)["\']', js)
print("main.js 內含 bond/cb 的路徑：")
for p in sorted(set(paths)):
    print(f"  {p}")

# 試幾個可能的報價頁面
price_pages = [
    '/web/bond/tradeinfo/cb/CB.php',
    '/web/bond/tradeinfo/cb/cbprice.php',
    '/web/bond/tradeinfo/cb/CBPrice.php',
    '/web/bond/tradeinfo/cb/cbMarket.php',
    '/web/bond/CB/cbprice.php',
    '/web/bond/CB/CB.php',
    '/zh-tw/bond-info/trading-info/cb',
]

print("\n試各報價頁面：")
for path in price_pages:
    url = 'https://www.tpex.org.tw' + path
    r = requests.get(url, headers=headers, timeout=8)
    title = re.search(r'<title>(.*?)</title>', r.content.decode('utf-8', errors='replace'))
    title_text = title.group(1) if title else '?'
    is_404 = '404' in title_text
    print(f"  {path} => {'404' if is_404 else title_text[:50]}")

    # 如果不是 404，找裡面的 action
    if not is_404:
        html = r.content.decode('utf-8', errors='replace')
        actions = re.findall(r'action\s*:\s*["\']([^"\']+)["\']', html)
        if actions:
            print(f"    actions: {actions}")
