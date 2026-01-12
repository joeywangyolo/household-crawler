# 專案架構規劃

## 最終目標
將爬蟲服務打包成 Docker，上傳到 GitLab，讓其他人可以：
1. `git clone` 下載
2. `docker-compose up` 一鍵啟動
3. 透過 API 或排程自動執行爬蟲

---

## 專案結構規劃

```
household-crawler/
├── docker-compose.yml          # 主要 Docker 設定
├── .env.example                # 環境變數範例
├── README.md                   # 使用說明
│
├── app/                        # 主應用程式
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── core/                   # 核心邏輯
│   │   ├── __init__.py
│   │   ├── crawler.py          # 爬蟲核心 (現在的 crawler_requests.py)
│   │   └── config.py           # 設定管理
│   ├── database/               # 資料庫
│   │   ├── __init__.py
│   │   ├── db_manager.py       # 資料庫操作
│   │   └── models.py           # 資料模型
│   └── tasks/                  # 排程任務
│       ├── __init__.py
│       ├── celery_app.py       # Celery 設定
│       └── scheduled_tasks.py  # 定時任務
│
├── database/                   # 資料庫初始化
│   └── init.sql
│
├── docker/                     # Docker 相關檔案
│   ├── Dockerfile.api          # API 服務 Docker
│   ├── Dockerfile.worker       # Celery Worker Docker
│   └── entrypoint.sh           # 啟動腳本
│
└── tests/                      # 測試
    └── test_crawler.py
```

---

## Docker 服務規劃

```yaml
services:
  # API 服務
  api:
    build: ./docker/Dockerfile.api
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis

  # Celery Worker (執行任務)
  worker:
    build: ./docker/Dockerfile.worker
    depends_on:
      - mysql
      - redis

  # Celery Beat (排程)
  beat:
    build: ./docker/Dockerfile.worker
    command: celery -A app.tasks beat
    depends_on:
      - worker

  # MySQL 資料庫
  mysql:
    image: mysql:8.0
    volumes:
      - mysql_data:/var/lib/mysql

  # Redis (Celery 訊息佇列)
  redis:
    image: redis:alpine

  # phpMyAdmin (可選)
  phpmyadmin:
    image: phpmyadmin
    ports:
      - "8080:80"
```

---

## API 規劃

### 1. 查詢相關
```
POST /api/query/district         # 查詢單一行政區
POST /api/query/batch            # 批量查詢所有行政區
GET  /api/query/history          # 查詢歷史記錄
GET  /api/query/{batch_id}       # 取得特定批次資料
```

### 2. 排程相關
```
GET  /api/schedule               # 取得排程設定
POST /api/schedule               # 新增排程
PUT  /api/schedule/{id}          # 修改排程
DELETE /api/schedule/{id}        # 刪除排程
POST /api/schedule/{id}/trigger  # 手動觸發排程
```

### 3. 資料相關
```
GET  /api/data/statistics        # 統計資料
GET  /api/data/export/csv        # 匯出 CSV
GET  /api/data/search            # 搜尋資料
```

---

## 排程設定 (Celery Beat)

```python
# app/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

app = Celery('household_crawler')

# 排程設定
app.conf.beat_schedule = {
    # 每天凌晨 2 點執行
    'daily-crawl': {
        'task': 'app.tasks.scheduled_tasks.crawl_all_districts',
        'schedule': crontab(hour=2, minute=0),
        'args': ('台北市',),
    },
    # 每週一執行完整爬取
    'weekly-full-crawl': {
        'task': 'app.tasks.scheduled_tasks.full_crawl',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
    },
}
```

---

## 開發階段

### 階段 1: 現在 ✅
- [x] 爬蟲核心邏輯 (crawler_requests.py)
- [x] MySQL 資料庫整合
- [x] OCR 驗證碼識別
- [x] 批量查詢功能

### 階段 2: API 化
- [ ] 建立 FastAPI 專案結構
- [ ] 將爬蟲邏輯包裝成 API
- [ ] 加入認證機制 (可選)

### 階段 3: 排程功能
- [ ] 整合 Celery
- [ ] 設定定時任務
- [ ] 加入任務監控 (Flower)

### 階段 4: Docker 打包
- [ ] 建立各服務 Dockerfile
- [ ] 整合 docker-compose
- [ ] 測試完整流程

### 階段 5: 上傳 GitLab
- [ ] 撰寫 README
- [ ] 建立 .env.example
- [ ] 上傳到 GitLab

---

## 驗證碼問題的解決方案

由於爬蟲需要驗證碼，在自動化排程中需要處理：

### 方案 1: OCR 自動識別 (目前使用)
- 使用 ddddocr 自動識別
- 成功率約 70-80%
- 失敗時記錄錯誤，下次排程再試

### 方案 2: 人工介入
- 排程執行時如果 OCR 失敗，發送通知
- 透過 API 讓管理員手動輸入驗證碼
- 適合低頻率的排程任務

### 方案 3: 打碼平台 (付費)
- 整合第三方打碼服務
- 準確率高，但需要費用

---

## 環境變數 (.env)

```bash
# 資料庫設定
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=household123
DB_NAME=household_db

# Redis 設定
REDIS_URL=redis://redis:6379/0

# API 設定
API_PORT=8000
API_SECRET_KEY=your-secret-key

# 爬蟲設定
OCR_ENABLED=true
OCR_MAX_RETRY=10

# 排程設定
SCHEDULE_ENABLED=true
SCHEDULE_TIMEZONE=Asia/Taipei
```

---

## 快速啟動指南 (給其他人用)

```bash
# 1. 複製專案
git clone https://gitlab.com/your-repo/household-crawler.git
cd household-crawler

# 2. 複製環境變數
cp .env.example .env
# 編輯 .env 設定

# 3. 啟動所有服務
docker-compose up -d

# 4. 查看服務狀態
docker-compose ps

# 5. 查看 API 文件
# 開啟瀏覽器: http://localhost:8000/docs
```
