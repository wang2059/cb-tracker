import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
from datetime import date, timedelta

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
           'Referer': 'https://www.tpex.org.tw/'}

def make_csv_url(target_date):
    y = target_date.year
    ym = target_date.strftime('%Y%m')
    ymd = target_date.strftime('%Y%m%d')
    return f'https://www.tpex.org.tw/storage/bond_zone/tradeinfo/cb/{y}/{ym}/RSta0113.{ymd}-C.csv'

# 往前找最近有資料的交易日
for days_back in range(0, 7):
    d = date.today() - timedelta(days=days_back)
    if d.weekday() >= 5:
        continue
    url = make_csv_url(d)
    print(f"嘗試 {d} => {url}")
    r = requests.get(url, headers=headers, timeout=15)
    print(f"狀態碼: {r.status_code} | Content-Type: {r.headers.get('Content-Type','')}")
    if r.status_code == 200:
        # 解碼 CSV（TPEX 通常用 Big5 或 UTF-8）
        for enc in ['big5', 'utf-8', 'cp950']:
            try:
                text = r.content.decode(enc)
                lines = [l for l in text.split('\n') if l.strip()]
                print(f"\n編碼: {enc}，共 {len(lines)} 行")
                print("前 5 行：")
                for line in lines[:5]:
                    print(f"  {line[:120]}")
                print(f"\n第 6-10 行：")
                for line in lines[5:10]:
                    print(f"  {line[:120]}")
                break
            except Exception:
                continue
        break
    print()
