import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 抓 TPEX 首頁找所有 href 含 bond 或 cb 的連結
r = requests.get('https://www.tpex.org.tw/web/index.php?l=zh-tw', headers=headers, timeout=15)
html = r.content.decode('utf-8', errors='replace')
links = re.findall(r'href=["\']([^"\']*(?:bond|cb|CB|convert)[^"\']*)["\']', html, re.IGNORECASE)
print("首頁 bond/CB 相關連結：")
for l in sorted(set(links)):
    print(f"  {l}")

# 也試 TPEX 的 bonds 頁面
r2 = requests.get('https://www.tpex.org.tw/web/bond/', headers=headers, timeout=10)
html2 = r2.content.decode('utf-8', errors='replace')
links2 = re.findall(r'href=["\']([^"\']+\.php[^"\']*)["\']', html2)
print("\nbonds/ 子頁面連結：")
for l in sorted(set(links2))[:30]:
    print(f"  {l}")

# 同時找 action 字串
actions = re.findall(r'action\s*:\s*["\']([^"\']+)["\']', html2)
print(f"\nbonds/ action 字串：{actions}")
