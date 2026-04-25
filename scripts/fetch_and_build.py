import requests
import json
import os
from datetime import date, timedelta

TOKEN = os.environ.get("FINMIND_TOKEN", "")
TODAY = date.today().strftime("%Y-%m-%d")

# FinMind 資料有時當天還沒更新，往前抓 5 天取最新一筆
def get_latest_data():
    for days_back in range(0, 6):
        target_date = (date.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        resp = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={
                "dataset": "TaiwanStockConvertibleBondDaily",
                "start_date": target_date,
                "end_date": target_date,
                "token": TOKEN,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data:
            print(f"取得資料日期：{target_date}，共 {len(data)} 筆")
            return data, target_date
    return [], TODAY

data, data_date = get_latest_data()

BUCKETS = {
    "100以下": [],
    "100-120": [],
    "120-135": [],
    "135-150": [],
    "150以上": [],
}

for row in data:
    try:
        price = float(row.get("close", 0))
    except (ValueError, TypeError):
        continue
    if price <= 0:
        continue

    bond_id = row.get("stock_id", "")
    bond_name = row.get("stock_name", bond_id)
    entry = {"id": bond_id, "name": bond_name, "price": price}

    if price < 100:
        BUCKETS["100以下"].append(entry)
    elif price < 120:
        BUCKETS["100-120"].append(entry)
    elif price < 135:
        BUCKETS["120-135"].append(entry)
    elif price < 150:
        BUCKETS["135-150"].append(entry)
    else:
        BUCKETS["150以上"].append(entry)

for bucket in BUCKETS.values():
    bucket.sort(key=lambda x: x["price"])

buckets_json = json.dumps(BUCKETS, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>台灣可轉債價格分布</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fa; color: #333; }}
    header {{ background: #1a3a5c; color: white; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }}
    header h1 {{ font-size: 1.2rem; font-weight: 600; }}
    header span {{ font-size: 0.85rem; opacity: 0.8; }}
    .layout {{ display: flex; height: calc(100vh - 56px); }}
    nav {{ width: 180px; min-width: 180px; background: #fff; border-right: 1px solid #e2e8f0; padding: 16px 0; }}
    nav button {{
      display: flex; justify-content: space-between; align-items: center;
      width: 100%; padding: 12px 16px; border: none; background: none;
      cursor: pointer; font-size: 0.95rem; color: #555; transition: background 0.15s;
      text-align: left;
    }}
    nav button:hover {{ background: #f0f4f8; }}
    nav button.active {{ background: #ebf4ff; color: #1a56db; font-weight: 600; border-left: 3px solid #1a56db; }}
    .badge {{
      background: #e2e8f0; color: #555; border-radius: 12px;
      padding: 2px 8px; font-size: 0.78rem; font-weight: 600; min-width: 28px; text-align: center;
    }}
    nav button.active .badge {{ background: #bfdbfe; color: #1a56db; }}
    main {{ flex: 1; overflow-y: auto; padding: 24px; }}
    .section-title {{ font-size: 1.1rem; font-weight: 600; color: #1a3a5c; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
    th {{ background: #f8fafc; padding: 12px 16px; text-align: left; font-size: 0.85rem; color: #64748b; font-weight: 600; border-bottom: 1px solid #e2e8f0; }}
    td {{ padding: 11px 16px; font-size: 0.92rem; border-bottom: 1px solid #f1f5f9; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f8fafc; }}
    .price {{ font-weight: 600; color: #c0392b; }}
    .empty {{ text-align: center; padding: 48px; color: #94a3b8; font-size: 0.95rem; }}
    @media (max-width: 600px) {{
      nav {{ width: 120px; min-width: 120px; }}
      nav button {{ font-size: 0.82rem; padding: 10px 10px; }}
      th, td {{ padding: 10px 10px; font-size: 0.85rem; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>台灣可轉債價格分布</h1>
    <span>資料日期：{data_date}</span>
  </header>
  <div class="layout">
    <nav id="nav"></nav>
    <main id="main"></main>
  </div>
  <script>
    const BUCKETS = {buckets_json};
    const LABELS = ["100以下", "100-120", "120-135", "135-150", "150以上"];
    let current = LABELS[1];

    function renderNav() {{
      const nav = document.getElementById("nav");
      nav.innerHTML = LABELS.map(label => `
        <button class="${{label === current ? 'active' : ''}}" onclick="select('${{label}}')" >
          <span>${{label}}</span>
          <span class="badge">${{BUCKETS[label].length}}</span>
        </button>
      `).join("");
    }}

    function renderMain() {{
      const bonds = BUCKETS[current];
      const main = document.getElementById("main");
      if (!bonds.length) {{
        main.innerHTML = `<div class="section-title">${{current}} 元</div><div class="empty">此區間目前無資料</div>`;
        return;
      }}
      main.innerHTML = `
        <div class="section-title">${{current}} 元（共 ${{bonds.length}} 檔）</div>
        <table>
          <thead><tr><th>代號</th><th>名稱</th><th>收盤價</th></tr></thead>
          <tbody>
            ${{bonds.map(b => `
              <tr>
                <td>${{b.id}}</td>
                <td>${{b.name}}</td>
                <td class="price">${{b.price.toFixed(2)}}</td>
              </tr>
            `).join("")}}
          </tbody>
        </table>
      `;
    }}

    function select(label) {{
      current = label;
      renderNav();
      renderMain();
    }}

    renderNav();
    renderMain();
  </script>
</body>
</html>
"""

out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"index.html 已產生，各區間筆數：")
for label, bonds in BUCKETS.items():
    print(f"  {label}: {len(bonds)} 筆")
