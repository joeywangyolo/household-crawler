# 戶政門牌資料爬蟲 API 使用說明

## 概述

本 API 提供戶政門牌資料的自動化查詢功能，使用 FastAPI 框架開發。

### 特點

- **自動化查詢**：驗證碼由系統自動處理 (OCR)，無需手動輸入
- **批量查詢**：支援一次查詢多個行政區
- **資料庫存儲**：可選擇將結果存入 MySQL 資料庫
- **自動文件**：內建 Swagger UI 和 ReDoc 文件

---

## 快速開始

### 本地啟動

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動 API 服務
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 啟動

```bash
# 啟動所有服務 (API + MySQL + phpMyAdmin)
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看 API 日誌
docker-compose logs -f api
```

### 服務端口

| 服務 | URL | 說明 |
|------|-----|------|
| API | http://localhost:8000 | FastAPI 服務 |
| Swagger UI | http://localhost:8000/docs | API 互動文件 |
| ReDoc | http://localhost:8000/redoc | API 文件 (閱讀模式) |
| phpMyAdmin | http://localhost:8080 | MySQL 管理介面 |

---

## API 端點

### 1. 健康檢查

檢查 API 服務和資料庫連線狀態。

```
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "timestamp": "2026-01-13T10:30:00"
}
```

---

### 2. 批量查詢 (主要功能)

一次查詢多個行政區的門牌資料。

```
POST /api/v1/query/batch
```

**Request Body:**
```json
{
  "city_code": "63000000",
  "start_date": "114-09-01",
  "end_date": "114-11-30",
  "register_kind": "1",
  "districts": null,
  "save_to_db": true
}
```

**參數說明:**

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `city_code` | string | 否 | 縣市代碼，預設 `63000000` (台北市) |
| `start_date` | string | **是** | 起始日期，民國年格式 (例: `114-09-01`) |
| `end_date` | string | **是** | 結束日期，民國年格式 (例: `114-11-30`) |
| `register_kind` | string | 否 | 編釘類別，預設 `1` (門牌初編) |
| `districts` | array | 否 | 指定行政區列表，`null` 表示全部 |
| `save_to_db` | boolean | 否 | 是否存入資料庫，預設 `true` |

**編釘類別對照:**
- `1` = 門牌初編
- `2` = 門牌改編
- `3` = 門牌廢止
- `4` = 門牌復用

**Response:**
```json
{
  "success": true,
  "batch_id": 123,
  "total_count": 2357,
  "district_results": {
    "松山區": 246,
    "信義區": 124,
    "大安區": 130,
    "中山區": 904,
    "中正區": 213,
    "大同區": 459,
    "萬華區": 111,
    "文山區": 170,
    "南港區": 0,
    "內湖區": 89,
    "士林區": 156,
    "北投區": 78
  },
  "failed_districts": [],
  "execution_time": 28.5,
  "data": null,
  "error_message": null
}
```

**注意事項:**
- 此操作可能需要 **20-30 秒** 完成
- 當資料超過 1000 筆時，`data` 欄位不會返回詳細資料
- 資料會自動存入資料庫 (如果 `save_to_db=true`)

---

### 3. 單一行政區查詢

查詢單一行政區的門牌資料。

```
POST /api/v1/query/district
```

**Request Body:**
```json
{
  "city_code": "63000000",
  "district_name": "松山區",
  "start_date": "114-09-01",
  "end_date": "114-11-30",
  "register_kind": "1"
}
```

**Response:**
```json
{
  "success": true,
  "district_name": "松山區",
  "total_count": 246,
  "data": [
    {
      "address": "臺北市松山區慈祐里014鄰八德路四段４８６號",
      "date": "民國114年10月29日",
      "type": "門牌初編",
      "district": "松山區"
    },
    ...
  ],
  "execution_time": 3.5,
  "error_message": null
}
```

---

### 4. 取得支援的行政區列表

```
GET /api/v1/districts
```

**Response:**
```json
{
  "city_name": "台北市",
  "city_code": "63000000",
  "districts": {
    "松山區": "63000010",
    "信義區": "63000020",
    "大安區": "63000030",
    "中山區": "63000040",
    "中正區": "63000050",
    "大同區": "63000060",
    "萬華區": "63000070",
    "文山區": "63000080",
    "南港區": "63000090",
    "內湖區": "63000100",
    "士林區": "63000110",
    "北投區": "63000120"
  }
}
```

---

### 5. 取得編釘類別列表

```
GET /api/v1/register-kinds
```

**Response:**
```json
{
  "register_kinds": {
    "1": "門牌初編",
    "2": "門牌改編",
    "3": "門牌廢止",
    "4": "門牌復用"
  }
}
```

---

## 使用範例

### cURL

```bash
# 健康檢查
curl http://localhost:8000/api/v1/health

# 批量查詢 (全部行政區)
curl -X POST http://localhost:8000/api/v1/query/batch \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "114-09-01",
    "end_date": "114-11-30"
  }'

# 批量查詢 (指定行政區)
curl -X POST http://localhost:8000/api/v1/query/batch \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "114-09-01",
    "end_date": "114-11-30",
    "districts": ["松山區", "信義區", "大安區"]
  }'

# 單一行政區查詢
curl -X POST http://localhost:8000/api/v1/query/district \
  -H "Content-Type: application/json" \
  -d '{
    "district_name": "松山區",
    "start_date": "114-09-01",
    "end_date": "114-11-30"
  }'
```

### Python

```python
import requests

# 批量查詢
response = requests.post(
    "http://localhost:8000/api/v1/query/batch",
    json={
        "start_date": "114-09-01",
        "end_date": "114-11-30",
        "districts": ["松山區", "信義區"]
    }
)

result = response.json()
print(f"總共找到 {result['total_count']} 筆資料")
print(f"執行時間: {result['execution_time']} 秒")
```

### JavaScript (Fetch)

```javascript
// 批量查詢
const response = await fetch('http://localhost:8000/api/v1/query/batch', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    start_date: '114-09-01',
    end_date: '114-11-30'
  })
});

const result = await response.json();
console.log(`總共找到 ${result.total_count} 筆資料`);
```

---

## 架構說明

### 專案結構

```
household-crawler/
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI 主程式
│   └── schemas.py        # Pydantic 資料模型
├── database/
│   ├── db_manager.py     # 資料庫管理模組
│   └── init.sql          # 資料表初始化腳本
├── crawler_requests.py   # 爬蟲核心邏輯
├── docker-compose.yml    # Docker 服務定義
├── Dockerfile            # API 容器定義
└── requirements.txt      # Python 依賴
```

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                                │
│              (瀏覽器 / Postman / 程式)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI (port 8000)                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  /api/v1/query/batch     → 批量查詢                  │    │
│  │  /api/v1/query/district  → 單一行政區查詢            │    │
│  │  /api/v1/districts       → 行政區列表               │    │
│  │  /api/v1/health          → 健康檢查                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  crawler_requests.py                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  HouseholdCrawler                                    │    │
│  │    ├─ init_session()      → 初始化爬蟲 session       │    │
│  │    ├─ query_all_pages()   → 分頁查詢                 │    │
│  │    └─ batch_query_all_districts() → 批量查詢         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│   戶政網站 (ris.gov.tw)   │    │   MySQL Database         │
│                          │    │   (household_db)          │
│  - 取得驗證碼             │    │                          │
│  - 送出查詢               │    │  - query_batches         │
│  - 取得結果               │    │  - household_records     │
│                          │    │  - district_results      │
└──────────────────────────┘    └──────────────────────────┘
```

### 資料流程

```
1. Client 發送 POST 請求到 /api/v1/query/batch
                    │
                    ▼
2. FastAPI 驗證請求參數 (Pydantic)
                    │
                    ▼
3. 建立 HouseholdCrawler 實例
                    │
                    ▼
4. 初始化 Session (打第一到第三層 API)
                    │
                    ▼
5. 取得驗證碼並 OCR 識別
                    │
                    ▼
6. 迴圈查詢每個行政區
   ├─ 第一個區: 使用驗證碼查詢
   └─ 後續區: 使用 token 查詢 (不需驗證碼)
                    │
                    ▼
7. 存入 MySQL 資料庫 (可選)
                    │
                    ▼
8. 返回查詢結果給 Client
```

---

## 錯誤處理

### HTTP 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 400 | 請求參數錯誤 |
| 500 | 伺服器內部錯誤 |

### 錯誤回應格式

```json
{
  "detail": "錯誤訊息說明"
}
```

---

## 注意事項

1. **執行時間**：批量查詢可能需要 20-30 秒，請設定足夠的 timeout
2. **驗證碼**：系統自動處理，OCR 可能偶爾失敗會自動重試
3. **日期格式**：使用民國年格式 (例: `114-09-01`)
4. **資料量**：當資料超過 1000 筆時，API 不會返回詳細資料，請從資料庫查詢

---

## 未來擴展

- [ ] 非同步任務支援 (BackgroundTasks)
- [ ] API Key 認證
- [ ] Rate Limiting
- [ ] 其他縣市支援
