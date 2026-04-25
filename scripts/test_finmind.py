import sys
import io
import requests
import json
from datetime import date, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ==============================
# 把你的 FinMind Token 貼在這裡
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoid2FuZ3d3dyIsImVtYWlsIjoidGFrZTU5MTc1M0BnbWFpbC5jb20ifQ.LQsj-Zsgf_uinRgnPuojQweKfLxH8fWr7oySqOGX7t4"
# ==============================

def test_cb_data():
    # 抓最近 3 天（確保有資料）
    start = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
    end   = date.today().strftime("%Y-%m-%d")

    print(f"抓取日期範圍：{start} ~ {end}\n")

    resp = requests.get(
        "https://api.finmindtrade.com/api/v4/data",
        params={
            "dataset": "TaiwanStockConvertibleBondDaily",
            "start_date": start,
            "end_date":   end,
            "token":      TOKEN,
        },
        timeout=30,
    )

    result = resp.json()

    if result.get("status") != 200:
        print("❌ API 錯誤：", result)
        return

    data = result.get("data", [])
    print(f"✅ 成功取得資料，共 {len(data)} 筆\n")

    if not data:
        print("⚠️  沒有資料，請確認日期或 Token 是否正確")
        return

    # 顯示欄位名稱
    print("=== 欄位清單 ===")
    print(list(data[0].keys()))
    print()

    # 顯示前 5 筆
    print("=== 前 5 筆資料範例 ===")
    for row in data[:5]:
        print(json.dumps(row, ensure_ascii=False))
    print()

    # 確認是否有漲跌幅欄位
    fields = list(data[0].keys())
    has_change = any(k in fields for k in ["change", "change_percent", "漲跌", "漲跌幅"])
    print(f"是否有漲跌幅欄位：{'✅ 有' if has_change else '❌ 沒有，需要自己計算'}")

    # 顯示日期清單（確認資料幾天）
    dates = sorted(set(row.get("date","") for row in data))
    print(f"\n資料包含日期：{dates}")

    # 顯示總共幾檔可轉債
    bonds = set(row.get("stock_id","") for row in data)
    print(f"總共幾檔可轉債：{len(bonds)} 檔")

if __name__ == "__main__":
    test_cb_data()
