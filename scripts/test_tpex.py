import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from datetime import date, timedelta

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.tpex.org.tw/",
}

today = date.today()
# 往前找最近交易日（避開週末）
for days_back in range(0, 7):
    d = today - timedelta(days=days_back)
    if d.weekday() < 5:  # 週一到週五
        roc_date = f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"
        break

print(f"測試日期：{roc_date}\n")

# --- 端點 1：TPEX OpenAPI ---
print("=== 端點 1：TPEX OpenAPI ===")
try:
    url = "https://www.tpex.org.tw/openapi/v1/tpex_cbtrademain"
    r = requests.get(url, headers=headers, timeout=15)
    print(f"狀態碼：{r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"筆數：{len(data)}")
        if data:
            print("欄位：", list(data[0].keys()))
            print("範例：", data[0])
except Exception as e:
    print(f"失敗：{e}")

print()

# --- 端點 2：TPEX OpenAPI (另一個名稱) ---
print("=== 端點 2：TPEX OpenAPI cb_daily ===")
try:
    url = "https://www.tpex.org.tw/openapi/v1/tpex_cb_daily_trading_statistics"
    r = requests.get(url, headers=headers, timeout=15)
    print(f"狀態碼：{r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"筆數：{len(data)}")
        if data:
            print("欄位：", list(data[0].keys()))
            print("範例：", data[0])
except Exception as e:
    print(f"失敗：{e}")

print()

# --- 端點 3：TPEX 舊版 AJAX ---
print("=== 端點 3：TPEX 舊版 AJAX ===")
try:
    url = "https://www.tpex.org.tw/web/bond/tradeinfo/cb/CBDaily.php"
    r = requests.get(url, params={"l":"zh-tw","d":roc_date,"o":"json"},
                     headers=headers, timeout=15)
    print(f"狀態碼：{r.status_code}")
    print(f"Content-Type：{r.headers.get('Content-Type','')}")
    text = r.text.strip()
    if text.startswith("{") or text.startswith("["):
        import json
        data = json.loads(text)
        print("JSON 成功，keys：", list(data.keys()) if isinstance(data,dict) else type(data))
    else:
        print("非 JSON，前 200 字：", text[:200])
except Exception as e:
    print(f"失敗：{e}")
