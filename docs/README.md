# 戶政司門牌查詢爬蟲 - 文件索引

## 📚 文件列表

### 1. [完整分析流程.md](./完整分析流程.md)
**最重要的文件！** 包含：
- 從零開始的完整分析流程
- 逐步測試 Requests 的方法
- Postman 測試指南（可以手動測試 API）
- 完整可執行的程式碼範例

**適合對象**：
- 需要了解整個爬蟲開發過程
- 想用 Postman 手動測試 API
- 需要向他人報告或教學

---

### 2. [F12_教學.md](./F12_教學.md)
瀏覽器開發者工具使用教學：
- 如何在 F12 Network 中找到 API
- 如何查看 Payload（POST 參數）
- 如何查看 Response（JSON 資料）
- 為什麼不用 BeautifulSoup

**適合對象**：
- 不熟悉 F12 開發者工具
- 想學習如何分析網站 API
- 需要理解現代爬蟲的分析方法

---

## 🎯 快速開始

### 如果你想快速使用爬蟲

直接執行：
```bash
python crawler_requests.py
```

### 如果你想理解整個流程

1. 先讀 [F12_教學.md](./F12_教學.md) 了解分析方法
2. 再讀 [完整分析流程.md](./完整分析流程.md) 看完整實作
3. 最後查看 `crawler_requests.py` 的程式碼

---

## 🔑 關鍵發現

### 1. 日期格式必須用破折號
```python
✓ 正確: "114-09-01"
✗ 錯誤: "114/09/01"
```

### 2. 必須按順序執行三個請求
```
GET  /info-doorplate/app/doorplate/main
  ↓ 取得 csrf_token_1
POST /info-doorplate/app/doorplate/map
  ↓ 取得 csrf_token_2
POST /info-doorplate/app/doorplate/query
  ↓ 取得 csrf_token_3 和 captcha_key
POST /info-doorplate/app/doorplate/inquiry/date
  ↓ 取得資料（JSON 格式）
```

### 3. 所有參數都要傳（包括空值）
查詢 API 需要 25 個參數，缺一不可

### 4. 資料是 JSON 格式
不需要 BeautifulSoup 解析 HTML，直接用 `resp.json()` 即可

---

## 🛠️ 工具和方法

### 分析工具
- **F12 Network**: 觀察網站請求
- **F12 Elements**: 查看 HTML 結構
- **Python requests**: 模擬瀏覽器請求
- **Postman**: 手動測試 API（可選）

### 爬蟲方法
- **傳統方法**: BeautifulSoup 解析 HTML DOM
- **我們的方法**: 逆向工程 API，直接呼叫後端

**為什麼用 API 方法？**
- 現代網站多用 AJAX 動態載入資料
- HTML 中沒有資料，只有空的容器
- API 回傳 JSON，更容易處理

---

## 📊 資料格式

### 查詢 API 回應
```json
{
  "records": 246,
  "total": 5,
  "page": 1,
  "rows": [
    {
      "v1": "臺北市松山區慈祐里014鄰八德路四段４８６號",
      "v2": "民國114年10月29日",
      "v3": "1"
    }
  ]
}
```

### 欄位說明
- `v1`: 完整地址
- `v2`: 編釘日期
- `v3`: 編釘類別（1=初編, 2=改編, 3=增編, 4=廢止）

---

## 🚀 進階使用

### 查詢不同區域
```python
crawler = HouseholdCrawler()
crawler.init_session("63000000")  # 台北市

# 松山區
result = crawler.query(area_code="63000010", ...)

# 信義區
result = crawler.query(area_code="63000020", ...)
```

### 查詢不同類別
```python
# 門牌初編
result = crawler.query(register_kind="1", ...)

# 門牌改編
result = crawler.query(register_kind="2", ...)

# 全部類別
result = crawler.query(register_kind="0", ...)
```

---

## ❓ 常見問題

### Q1: 為什麼驗證碼一直錯誤？
- 確認大小寫正確
- 驗證碼有時效性，取得後立即使用
- 如果失敗，需要重新取得新的 captcha_key

### Q2: 為什麼查無資料？
- 檢查日期格式（必須用破折號）
- 確認區域代碼正確
- 該時間區間可能真的沒有資料

### Q3: 可以用 Postman 測試嗎？
可以！詳見 [完整分析流程.md](./完整分析流程.md) 的 Postman 測試指南

### Q4: 為什麼不用 Selenium？
- Requests 更輕量、更快
- 不需要啟動瀏覽器
- 適合大量查詢

---

## 📝 專案結構

```
household-crawler/
├── docs/                          # 📚 文件資料夾
│   ├── README.md                  # 本文件
│   ├── 完整分析流程.md             # 完整教學
│   └── F12_教學.md                # F12 使用指南
├── crawler_requests.py            # ✅ 主要爬蟲（推薦使用）
├── test_fixed.py                  # 測試腳本
├── analyze_network.py             # 分析腳本
└── step1-3_*.html                 # 各階段的 HTML 檔案
```

---

## 🎓 學習路徑

### 初學者
1. 閱讀 [F12_教學.md](./F12_教學.md)
2. 執行 `analyze_network.py` 看實際流程
3. 查看產生的 HTML 檔案
4. 執行 `crawler_requests.py` 測試

### 進階使用者
1. 閱讀 [完整分析流程.md](./完整分析流程.md)
2. 用 Postman 手動測試 API
3. 修改 `crawler_requests.py` 加入新功能
4. 整合到自己的專案

---

## 📧 技術支援

如有問題，請參考：
1. 文件中的「常見問題」章節
2. 程式碼中的註解
3. `test_fixed.py` 的測試範例

---

**最後更新**: 2026/01/07
**版本**: 1.0
**狀態**: ✅ 測試通過，可正常使用
