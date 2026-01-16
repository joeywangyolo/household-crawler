# Batch ID 與 Log 資料流文件

## 資料庫結構

### 表格關聯圖

```
┌─────────────────────────┐
│     crawler_logs        │
│  (主表，產生 batch_id)   │
│─────────────────────────│
│  id (PK) ←── batch_id   │
│  api_endpoint           │
│  start_time             │
│  end_time               │
│  records_fetched        │
│  status                 │
│  error_message          │
│  created_at             │
└───────────┬─────────────┘
            │
            │ id = batch_id (外鍵關聯)
            │
    ┌───────┴───────┐
    ↓               ↓
┌─────────────┐  ┌─────────────────────┐
│ household_  │  │ district_query_     │
│ records     │  │ results             │
│─────────────│  │─────────────────────│
│ id (PK)     │  │ id (PK)             │
│ batch_id(FK)│  │ batch_id (FK)       │
│ city        │  │ city_name           │
│ district    │  │ district_code       │
│ full_address│  │ district_name       │
│ edit_date   │  │ record_count        │
│ ...         │  │ status              │
└─────────────┘  │ error_message       │
                 └─────────────────────┘
```

### SQL 定義 (database/init.sql)

```sql
-- crawler_logs: 第 15-26 行
CREATE TABLE IF NOT EXISTS crawler_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '批次 ID (batch_id)',
    api_endpoint VARCHAR(100) COMMENT 'API 端點',
    start_time DATETIME COMMENT '開始時間',
    end_time DATETIME COMMENT '結束時間',
    records_fetched INT DEFAULT 0 COMMENT '擷取記錄數',
    status ENUM('running', 'completed', 'failed') DEFAULT 'running' COMMENT '狀態',
    error_message TEXT COMMENT '錯誤訊息',
    ...
);

-- household_records: 第 31-47 行
CREATE TABLE IF NOT EXISTS household_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT COMMENT '批次 ID，關聯 crawler_logs.id',
    ...
    FOREIGN KEY (batch_id) REFERENCES crawler_logs(id) ON DELETE SET NULL
);

-- district_query_results: 第 52-67 行
CREATE TABLE IF NOT EXISTS district_query_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT COMMENT '批次 ID，關聯 crawler_logs.id',
    ...
    FOREIGN KEY (batch_id) REFERENCES crawler_logs(id) ON DELETE CASCADE
);
```

---

## Batch ID 資料流

### 流程圖

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. API 層 (api/main.py)                                            │
│     第 174 行: batch_id = db_manager.start_log("/api/v1/query/batch")│
│                          ↓                                          │
│     產生 batch_id (crawler_logs.id 自動遞增)                         │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  2. 爬蟲層 (crawler_requests.py)                                    │
│     第 181-188 行:                                                  │
│     crawler.batch_query_all_districts(..., batch_id=batch_id)       │
│                          ↓                                          │
│     傳遞 batch_id 給資料庫操作                                       │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  3. 資料庫層 (database/db_manager.py)                               │
│     第 753-758 行 (crawler_requests.py 內呼叫):                     │
│     db_manager.insert_records(batch_id, city, district, records)    │
│     db_manager.insert_district_result(batch_id, ...)                │
│                          ↓                                          │
│     寫入 household_records 和 district_query_results                │
└─────────────────────────────────────────────────────────────────────┘
```

### 詳細程式碼位置

| 步驟 | 檔案 | 行號 | 說明 |
|------|------|------|------|
| 產生 batch_id | api/main.py | 174 | `batch_id = db_manager.start_log(...)` |
| start_log 實作 | database/db_manager.py | 259-280 | INSERT 到 crawler_logs，回傳 lastrowid |
| 傳遞給爬蟲 | api/main.py | 181-188 | `batch_query_all_districts(..., batch_id=batch_id)` |
| 爬蟲接收參數 | crawler_requests.py | 660-668 | 函數定義 `batch_id: int = None` |
| 寫入 records | crawler_requests.py | 753-754 | `db_manager.insert_records(batch_id, ...)` |
| 寫入 district | crawler_requests.py | 755-758 | `db_manager.insert_district_result(batch_id, ...)` |
| insert_records 實作 | database/db_manager.py | 206-256 | INSERT 到 household_records |
| insert_district_result 實作 | database/db_manager.py | 166-201 | INSERT 到 district_query_results |

---

## Log 資料流

### 流程圖

```
┌─────────────────────────────────────────────────────────────────────┐
│  API 呼叫 /api/v1/query/batch                                       │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: start_log() — 建立 log 記錄                                │
│  檔案: api/main.py 第 174 行                                        │
│  INSERT INTO crawler_logs (api_endpoint, start_time, status)        │
│  status = 'running'                                                 │
│  回傳 batch_id (= crawler_logs.id)                                  │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: 執行爬蟲查詢（不管查 1 區或 12 區）                          │
│  → 寫入 household_records (帶 batch_id)                             │
│  → 寫入 district_query_results (帶 batch_id)                        │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: end_log() — 更新 log 記錄                                  │
│  檔案: api/main.py 第 192-194 行                                    │
│  UPDATE crawler_logs SET end_time, records_fetched, status          │
│  status = 'completed' 或 'failed'                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### start_log 實作 (database/db_manager.py 第 259-280 行)

```python
def start_log(self, api_endpoint: str) -> Optional[int]:
    sql = """
        INSERT INTO crawler_logs (api_endpoint, start_time, status)
        VALUES (%s, NOW(), 'running')
    """
    cursor.execute(sql, (api_endpoint,))
    log_id = cursor.lastrowid  # ← 這就是 batch_id (AUTO_INCREMENT)
    return log_id
```

### end_log 實作 (database/db_manager.py 第 282-308 行)

```python
def end_log(self, log_id: int, records_fetched: int = 0, 
            status: str = "completed", error_message: str = None):
    sql = """
        UPDATE crawler_logs 
        SET end_time = NOW(), records_fetched = %s, status = %s, error_message = %s
        WHERE id = %s
    """
    cursor.execute(sql, (records_fetched, status, error_message, log_id))
```

---

## 單區查詢也會記錄 Log

使用 `/api/v1/query/batch` 即使只查詢單一行政區，也會完整記錄 log：

```json
// 請求
{
  "districts": ["中正區"],
  "start_date": "1140101",
  "end_date": "1140115",
  "save_to_db": true
}
```

結果：
- `crawler_logs`: 1 筆 (batch_id = N)
- `district_query_results`: 1 筆 (batch_id = N)
- `household_records`: X 筆 (全部 batch_id = N)

---

## 目前保留的 API Endpoints

| Endpoint | 用途 |
|----------|------|
| `/api/v1/health` | 健康檢查 |
| `/api/v1/query/batch` | 批量查詢（支援單區或多區） |
| `/api/v1/districts` | 取得支援的行政區列表 |
