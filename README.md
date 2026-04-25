# 台灣可轉債價格分布

每日自動抓取台灣全市場可轉債收盤價，依價格區間分類顯示。

## 設定步驟（只需做一次）

1. 把這個 repo Push 到你的 GitHub
2. 到 repo 的 **Settings → Secrets and variables → Actions**
3. 點 **New repository secret**，名稱填 `FINMIND_TOKEN`，值貼上你的 FinMind API Token
4. 到 **Settings → Pages**，Source 選 `Deploy from a branch`，Branch 選 `main`，Folder 選 `/docs`
5. 到 **Actions** 頁面，手動觸發一次 `Update CB Data` 確認正常運作

## 資料來源
- FinMind API `TaiwanStockConvertibleBondDaily`
- 每個交易日 15:30 後自動更新
