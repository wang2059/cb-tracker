import sys, io, os, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from datetime import date, timedelta

# 載入產業對照表
INDUSTRY_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'industry_map.json')
if os.path.exists(INDUSTRY_MAP_PATH):
    with open(INDUSTRY_MAP_PATH, 'r', encoding='utf-8') as _f:
        INDUSTRY_MAP = json.load(_f)
else:
    INDUSTRY_MAP = {}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tpex.org.tw/',
}

def make_csv_url(d):
    y  = d.strftime('%Y')
    ym = d.strftime('%Y%m')
    ymd = d.strftime('%Y%m%d')
    return f'https://www.tpex.org.tw/storage/bond_zone/tradeinfo/cb/{y}/{ym}/RSta0113.{ymd}-C.csv'

def fetch_csv(target_date):
    for days_back in range(0, 8):
        d = target_date - timedelta(days=days_back)
        if d.weekday() >= 5:
            continue
        url = make_csv_url(d)
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and len(r.content) > 500:
            print(f"取得資料：{d}（{url}）")
            return r.content, d
    return None, None

def parse_csv(raw_bytes):
    text = raw_bytes.decode('big5', errors='replace')
    bonds = []
    for line in text.split('\n'):
        line = line.strip()
        if not line.startswith('BODY'):
            continue
        # 去掉開頭的 BODY,
        row_text = line[5:]
        # 用 csv 解析含引號的欄位
        try:
            cols = next(csv.reader([row_text]))
        except Exception:
            continue
        if len(cols) < 5:
            continue

        bond_id   = cols[0].strip()
        bond_name = cols[1].strip()
        trade_type = cols[2].strip()
        close_str  = cols[3].strip()
        change_str = cols[4].strip()
        volume_str = cols[9].strip() if len(cols) > 9 else ''

        # 只取等價交易、有代號、有收盤價的行
        if trade_type != '等價' or not bond_id or not close_str:
            continue

        try:
            close = float(close_str.replace(',', ''))
        except ValueError:
            continue

        # 漲跌點數（可能空白 = 0）
        try:
            change_pts = float(change_str.replace(',', '').replace('+', ''))
        except ValueError:
            change_pts = 0.0

        # 計算漲跌%
        yesterday_close = close - change_pts
        if yesterday_close and yesterday_close != 0:
            change_pct = round(change_pts / yesterday_close * 100, 2)
        else:
            change_pct = 0.0

        try:
            volume = int(volume_str.replace(',', '').strip())
        except ValueError:
            volume = 0

        stock_id = bond_id[:4]
        info = INDUSTRY_MAP.get(stock_id, {})
        bonds.append({
            'id':         bond_id,
            'name':       bond_name,
            'price':      close,
            'change_pts': change_pts,
            'change_pct': change_pct,
            'volume':     volume,
            'industry':   info.get('industry', ''),
            'chain':      info.get('chain', ''),
        })

    return bonds

def get_bucket(price):
    if price < 100:   return 'u100'
    if price < 120:   return '100-120'
    if price < 135:   return '120-135'
    if price < 150:   return '135-150'
    return 'o150'

def get_color(pct):
    if pct >= 8.5:  return '#7f0000', '#fff'
    if pct >= 6.5:  return '#d32f2f', '#fff'
    if pct >= 5.0:  return '#ef9a9a', '#333'
    if pct >= 3.0:  return '#ffcdd2', '#555'
    if pct > 0:     return '#fff5f5', '#777'
    if pct == 0:    return '#f8fafc', '#555'
    if pct > -3.0:  return '#f5fff7', '#777'
    if pct >= -5.0: return '#c8e6c9', '#1a3a1a'
    if pct >= -6.5: return '#81c784', '#1a3a1a'
    if pct >= -8.5: return '#2e7d32', '#fff'
    return '#1b5e20', '#fff'

def fmt_pts(pts):
    if pts > 0:   return f'▲ {pts:.2f} 點'
    if pts < 0:   return f'▼ {abs(pts):.2f} 點'
    return '－ 平盤'

def fmt_pct(pct):
    if pct > 0:   return f'（+{pct:.2f}%）'
    if pct < 0:   return f'（{pct:.2f}%）'
    return '（0.00%）'

# ── 主流程 ──────────────────────────────────────────────
raw, data_date = fetch_csv(date.today())
if raw is None:
    print("錯誤：無法取得 CSV 資料")
    sys.exit(1)

bonds = parse_csv(raw)
print(f"解析完成，共 {len(bonds)} 檔可轉債")

# 依漲跌幅排序（高到低）
bonds.sort(key=lambda x: x['change_pct'], reverse=True)

# 統計
up   = sum(1 for b in bonds if b['change_pct'] > 0)
down = sum(1 for b in bonds if b['change_pct'] < 0)
flat = sum(1 for b in bonds if b['change_pct'] == 0)
top  = bonds[0]['change_pct'] if bonds else 0
bot  = bonds[-1]['change_pct'] if bonds else 0

bucket_counts = {'u100':0,'100-120':0,'120-135':0,'135-150':0,'o150':0}
for b in bonds:
    bucket_counts[get_bucket(b['price'])] += 1

date_str = data_date.strftime('%Y-%m-%d')
bonds_json = json.dumps(bonds, ensure_ascii=False)

def fmt_change_display(pts, pct):
    pts_str = fmt_pts(pts)
    pct_str = fmt_pct(pct)
    return f'{pts_str} {pct_str}'

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>台灣可轉債熱力圖</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft JhengHei", sans-serif; background: #f0f4f8; color: #222; }}
    header {{
      background: #0f2942; color: #fff;
      padding: 0 24px; height: 52px;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 100;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
    header h1 {{ font-size: 1.05rem; font-weight: 700; }}
    header .meta {{ font-size: 0.8rem; color: #94b8d8; }}
    .layout {{ display: flex; height: calc(100vh - 52px); }}
    nav {{
      width: 190px; min-width: 190px; background: #fff;
      border-right: 1px solid #dde4ed;
      display: flex; flex-direction: column; overflow-y: auto;
    }}
    .nav-section-title {{
      font-size: 0.72rem; font-weight: 700; color: #94a3b8;
      letter-spacing: 1px; padding: 16px 16px 6px;
    }}
    nav button {{
      display: flex; justify-content: space-between; align-items: center;
      width: 100%; padding: 10px 16px;
      border: none; background: none; cursor: pointer;
      font-size: 0.9rem; color: #475569;
      transition: background 0.12s; text-align: left;
      border-left: 3px solid transparent;
    }}
    nav button:hover {{ background: #f1f5f9; }}
    nav button.active {{ background: #eff6ff; color: #1d4ed8; font-weight: 600; border-left-color: #2563eb; }}
    .badge {{
      background: #e2e8f0; color: #64748b;
      border-radius: 10px; padding: 2px 9px;
      font-size: 0.75rem; font-weight: 700;
    }}
    nav button.active .badge {{ background: #bfdbfe; color: #1d4ed8; }}
    .nav-divider {{ height: 1px; background: #e8edf4; margin: 8px 0; }}
    .legend {{ padding: 12px 14px 16px; border-top: 1px solid #e8edf4; margin-top: auto; }}
    .legend-title {{ font-size: 0.7rem; color: #94a3b8; font-weight: 700; letter-spacing: 0.8px; margin-bottom: 8px; }}
    .legend-row {{ display: flex; align-items: center; gap: 6px; margin-bottom: 4px; font-size: 0.75rem; color: #64748b; }}
    .legend-swatch {{ width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }}
    main {{ flex: 1; overflow-y: auto; padding: 20px 24px; }}
    .stats-bar {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
    .stat-box {{
      background: #fff; border-radius: 8px; padding: 10px 16px;
      border: 1px solid #e2e8f0; flex: 1; min-width: 100px; text-align: center;
    }}
    .stat-label {{ font-size: 0.72rem; color: #94a3b8; font-weight: 600; }}
    .stat-value {{ font-size: 1.05rem; font-weight: 800; margin-top: 2px; }}
    .stat-value.up {{ color: #dc2626; }}
    .stat-value.down {{ color: #16a34a; }}
    .stat-value.neutral {{ color: #475569; }}
    .main-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }}
    .main-title {{ font-size: 1rem; font-weight: 700; color: #1e3a5f; }}
    .main-sub {{ font-size: 0.8rem; color: #94a3b8; }}
    .sort-select {{
      font-size: 0.82rem; color: #475569; background: #fff;
      border: 1px solid #e2e8f0; padding: 5px 10px;
      border-radius: 8px; cursor: pointer; outline: none;
    }}
    .sort-select:hover {{ border-color: #94a3b8; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(152px, 1fr)); gap: 8px; }}
    .card {{
      border-radius: 8px; padding: 11px 12px 10px;
      cursor: default; transition: transform 0.12s, box-shadow 0.12s;
    }}
    .card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.15); }}
    .card-name {{ font-size: 0.9rem; font-weight: 700; display: flex; align-items: baseline; gap: 5px; margin-bottom: 2px; }}
    .card-name span.name-text {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }}
    .card-code {{ font-size: 0.7rem; opacity: 0.7; font-weight: 500; flex-shrink: 0; }}
    .card-meta {{ font-size: 0.7rem; opacity: 0.82; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 8px; min-height: 14px; }}
    .card-price-row {{ font-size: 0.8rem; opacity: 0.9; margin-bottom: 3px; }}
    .card-price-val {{ font-weight: 700; }}
    .card-change {{ font-size: 0.82rem; font-weight: 700; }}
    .card-volume {{ font-size: 0.7rem; opacity: 0.72; text-align: right; margin-top: 3px; }}
    .empty {{ text-align: center; padding: 60px; color: #94a3b8; grid-column: 1/-1; }}
  </style>
</head>
<body>
<header>
  <h1>台灣可轉債熱力圖</h1>
  <span class="meta">資料日期：{date_str}　共 {len(bonds)} 檔</span>
</header>
<div class="layout">
  <nav>
    <div class="nav-section-title">價格分布</div>
    <button class="active" onclick="filterBy('all',this)">
      <span>全部</span><span class="badge">{len(bonds)}</span>
    </button>
    <button onclick="filterBy('u100',this)">
      <span>100 以下</span><span class="badge">{bucket_counts['u100']}</span>
    </button>
    <button onclick="filterBy('100-120',this)">
      <span>100–120</span><span class="badge">{bucket_counts['100-120']}</span>
    </button>
    <button onclick="filterBy('120-135',this)">
      <span>120–135</span><span class="badge">{bucket_counts['120-135']}</span>
    </button>
    <button onclick="filterBy('135-150',this)">
      <span>135–150</span><span class="badge">{bucket_counts['135-150']}</span>
    </button>
    <button onclick="filterBy('o150',this)">
      <span>150 以上</span><span class="badge">{bucket_counts['o150']}</span>
    </button>
    <div class="nav-divider"></div>
    <div class="legend">
      <div class="legend-title">漲跌色階</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#7f0000"></div>深紅 ≥8.5%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#d32f2f"></div>中紅 6.5–8.4%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#ef9a9a"></div>淡紅 5–6.4%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#ffcdd2"></div>更淡紅 3–4.9%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#fff5f5;border:1px solid #eee"></div>紅白底 0–2.9%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#f5fff7;border:1px solid #eee"></div>綠白底 0–2.9%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#c8e6c9"></div>更淡綠 3–4.9%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#81c784"></div>淡綠 5–6.4%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#2e7d32"></div>中綠 6.5–8.4%</div>
      <div class="legend-row"><div class="legend-swatch" style="background:#1b5e20"></div>深綠 ≥8.5%</div>
    </div>
  </nav>
  <main>
    <div class="stats-bar">
      <div class="stat-box"><div class="stat-label">上漲</div><div class="stat-value up" id="s-up">{up} 檔</div></div>
      <div class="stat-box"><div class="stat-label">下跌</div><div class="stat-value down" id="s-down">{down} 檔</div></div>
      <div class="stat-box"><div class="stat-label">平盤</div><div class="stat-value neutral" id="s-flat">{flat} 檔</div></div>
      <div class="stat-box"><div class="stat-label">最大漲幅</div><div class="stat-value up" id="s-top">+{top:.2f}%</div></div>
      <div class="stat-box"><div class="stat-label">最大跌幅</div><div class="stat-value down" id="s-bot">{bot:.2f}%</div></div>
    </div>
    <div class="main-header">
      <div>
        <div class="main-title" id="grid-title">全部可轉債（{len(bonds)} 檔）</div>
        <div class="main-sub">依漲跌幅由高至低排列</div>
      </div>
      <select class="sort-select" id="sort-select" onchange="changeSort(this.value)">
        <option value="change">↕ 漲跌幅排序</option>
        <option value="volume">↕ 成交量排序</option>
      </select>
    </div>
    <div class="grid" id="grid"></div>
  </main>
</div>
<script>
const BONDS = {bonds_json};
const COLOR_MAP = {{}};

function getBucket(price) {{
  if (price < 100)  return 'u100';
  if (price < 120)  return '100-120';
  if (price < 135)  return '120-135';
  if (price < 150)  return '135-150';
  return 'o150';
}}

function getColor(pct) {{
  if (pct >= 8.5)  return ['#7f0000','#fff'];
  if (pct >= 6.5)  return ['#d32f2f','#fff'];
  if (pct >= 5.0)  return ['#ef9a9a','#333'];
  if (pct >= 3.0)  return ['#ffcdd2','#555'];
  if (pct > 0)     return ['#fff5f5','#777'];
  if (pct === 0)   return ['#f8fafc','#555'];
  if (pct > -3.0)  return ['#f5fff7','#777'];
  if (pct >= -5.0) return ['#c8e6c9','#1a3a1a'];
  if (pct >= -6.5) return ['#81c784','#1a3a1a'];
  if (pct >= -8.5) return ['#2e7d32','#fff'];
  return ['#1b5e20','#fff'];
}}

function fmtPts(pts) {{
  if (pts > 0) return '▲ ' + pts.toFixed(2) + ' 點';
  if (pts < 0) return '▼ ' + Math.abs(pts).toFixed(2) + ' 點';
  return '－ 平盤';
}}

function fmtPct(pct) {{
  if (pct > 0) return '（+' + pct.toFixed(2) + '%）';
  if (pct < 0) return '（' + pct.toFixed(2) + '%）';
  return '（0.00%）';
}}

let currentFilter = 'all';
let currentSort   = 'change';

function changeSort(val) {{
  currentSort = val;
  const sub = document.querySelector('.main-sub');
  sub.textContent = val === 'volume' ? '依成交量由高至低排列' : '依漲跌幅由高至低排列';
  renderGrid();
}}

function filterBy(bucket, btn) {{
  currentFilter = bucket;
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderGrid();
}}

function renderGrid() {{
  const filtered = (currentFilter === 'all'
    ? [...BONDS]
    : BONDS.filter(b => getBucket(b.price) === currentFilter));

  if (currentSort === 'volume') {{
    filtered.sort((a, b) => b.volume - a.volume);
  }} else {{
    filtered.sort((a, b) => b.change_pct - a.change_pct);
  }}

  const titles = {{
    all:'全部可轉債', 'u100':'100 以下',
    '100-120':'100–120 元', '120-135':'120–135 元',
    '135-150':'135–150 元', 'o150':'150 元以上'
  }};
  document.getElementById('grid-title').textContent = titles[currentFilter] + '（' + filtered.length + ' 檔）';

  const grid = document.getElementById('grid');
  if (!filtered.length) {{
    grid.innerHTML = '<div class="empty">此區間目前無資料</div>';
    return;
  }}

  grid.innerHTML = filtered.map(b => {{
    const [bg, fg] = getColor(b.change_pct);
    const industry = [b.industry, b.chain].filter(Boolean).join(' · ');
    const ptsStr = fmtPts(b.change_pts);
    const pctStr = fmtPct(b.change_pct);
    return `<div class="card" style="background:${{bg}};color:${{fg}};">
      <div class="card-name"><span class="name-text">${{b.name}}</span><span class="card-code">${{b.id}}</span></div>
      <div class="card-meta">${{industry || '&nbsp;'}}</div>
      <div class="card-price-row">收盤 <span class="card-price-val">${{b.price.toFixed(2)}}</span></div>
      <div class="card-change">${{ptsStr}} ${{pctStr}}</div>
      <div class="card-volume">成交量 ${{b.volume > 0 ? b.volume.toLocaleString() + ' 張' : '-'}}</div>
    </div>`;
  }}).join('');
}}

renderGrid();
</script>
</body>
</html>
"""

out_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n完成！index.html 已產生（{len(bonds)} 檔）")
print(f"上漲 {up} 檔，下跌 {down} 檔，平盤 {flat} 檔")
print(f"最大漲幅：+{top:.2f}%，最大跌幅：{bot:.2f}%")
