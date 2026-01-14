"""
戶政門牌資料爬蟲 API
使用 FastAPI 框架

啟動方式:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

API 文件:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""
import sys
import os
import time
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# 加入專案根目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    BatchQueryRequest,
    BatchQueryResponse,
    DistrictQueryRequest,
    DistrictQueryResponse,
    HealthResponse,
    ErrorResponse,
    HouseholdRecord
)
from crawler_requests import HouseholdCrawler

# 嘗試載入資料庫模組
try:
    from database.db_manager import DatabaseManager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# ============================================================
# FastAPI 應用程式
# ============================================================

app = FastAPI(
    title="戶政門牌資料爬蟲 API",
    description="""
## 功能說明

此 API 提供戶政門牌資料的自動化查詢功能，支援：

- **批量查詢**：一次查詢多個行政區的門牌資料
- **單一查詢**：查詢單一行政區的門牌資料
- **資料庫存儲**：可選擇將結果存入 MySQL 資料庫

## 注意事項

- 批量查詢可能需要 20-30 秒，請耐心等待
- 驗證碼由系統自動處理 (OCR)，無需手動輸入
- 日期格式使用民國年 (例如: 114-09-01)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 健康檢查
# ============================================================

@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["系統"],
    summary="健康檢查"
)
def health_check():
    """
    檢查 API 服務和資料庫連線狀態
    """
    db_status = "unavailable"
    
    if DB_AVAILABLE:
        try:
            db = DatabaseManager()
            if db.connect():
                db_status = "connected"
                db.close()
            else:
                db_status = "connection_failed"
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        version="1.0.0",
        timestamp=datetime.now()
    )


# ============================================================
# 批量查詢
# ============================================================

@app.post(
    "/api/v1/query/batch",
    response_model=BatchQueryResponse,
    responses={
        200: {"description": "查詢成功"},
        500: {"model": ErrorResponse, "description": "伺服器錯誤"}
    },
    tags=["查詢"],
    summary="批量查詢多個行政區"
)
def batch_query(request: BatchQueryRequest):
    """
    批量查詢指定縣市的多個行政區門牌資料
    
    - **city_code**: 縣市代碼 (預設: 63000000 台北市)
    - **start_date**: 起始日期 (民國年格式: 114-09-01)
    - **end_date**: 結束日期 (民國年格式: 114-11-30)
    - **register_kind**: 編釘類別 (1=初編, 2=改編, 3=廢止, 4=復用)
    - **districts**: 指定行政區列表，null 表示全部
    - **save_to_db**: 是否存入資料庫
    
    注意: 此操作可能需要 20-30 秒完成
    """
    start_time = time.time()
    
    try:
        # 建立爬蟲實例
        crawler = HouseholdCrawler(use_ocr=True)
        
        # 初始化 session
        if not crawler.init_session():
            raise HTTPException(status_code=500, detail="無法初始化爬蟲 session")
        
        # 決定要查詢的行政區
        if request.districts:
            # 過濾出有效的行政區
            districts = {
                name: code 
                for name, code in crawler.TAIPEI_DISTRICTS.items() 
                if name in request.districts
            }
            if not districts:
                raise HTTPException(
                    status_code=400, 
                    detail=f"無效的行政區: {request.districts}"
                )
        else:
            districts = crawler.TAIPEI_DISTRICTS
        
        # 資料庫連線和 batch_id
        db_manager = None
        batch_id = None
        if request.save_to_db and DB_AVAILABLE:
            try:
                db_manager = DatabaseManager()
                if db_manager.connect():
                    # 建立 log 記錄，取得 batch_id
                    batch_id = db_manager.start_log("/api/v1/query/batch")
                else:
                    db_manager = None
            except:
                db_manager = None
        
        # 執行批量查詢
        result = crawler.batch_query_all_districts(
            districts=districts,
            start_date=request.start_date,
            end_date=request.end_date,
            register_kind=request.register_kind,
            city_name="台北市",
            db_manager=db_manager,
            batch_id=batch_id
        )
        
        # 更新 log 狀態並關閉資料庫連線
        if db_manager and batch_id:
            status = "completed" if result.success else "failed"
            db_manager.end_log(batch_id, result.total_count, status, result.error_message)
        if db_manager:
            db_manager.close()
        
        execution_time = time.time() - start_time
        
        # 整理失敗的行政區
        failed_districts = [
            name for name, count in result.district_results.items() 
            if count == -1
        ]
        
        # 整理成功的行政區結果
        district_results = {
            name: count 
            for name, count in result.district_results.items() 
            if count >= 0
        }
        
        # 轉換資料格式
        records = [
            HouseholdRecord(
                address=item.get("address", ""),
                date=item.get("date", ""),
                type=item.get("type", ""),
                district=item.get("district", "")
            )
            for item in result.all_data
        ] if result.all_data else []
        
        return BatchQueryResponse(
            success=result.success,
            total_count=result.total_count,
            district_results=district_results,
            failed_districts=failed_districts,
            execution_time=round(execution_time, 2),
            data=records if len(records) <= 300 else None,  # 超過 1000 筆不返回詳細資料
            error_message=result.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 單一行政區查詢
# ============================================================

@app.post(
    "/api/v1/query/district",
    response_model=DistrictQueryResponse,
    responses={
        200: {"description": "查詢成功"},
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        500: {"model": ErrorResponse, "description": "伺服器錯誤"}
    },
    tags=["查詢"],
    summary="查詢單一行政區"
)
def district_query(request: DistrictQueryRequest):
    """
    查詢單一行政區的門牌資料
    
    - **district_name**: 行政區名稱 (例如: 松山區)
    - **start_date**: 起始日期
    - **end_date**: 結束日期
    """
    start_time = time.time()
    
    try:
        crawler = HouseholdCrawler(use_ocr=True)
        
        if not crawler.init_session():
            raise HTTPException(status_code=500, detail="無法初始化爬蟲 session")
        
        # 取得行政區代碼
        area_code = crawler.TAIPEI_DISTRICTS.get(request.district_name)
        if not area_code:
            raise HTTPException(
                status_code=400,
                detail=f"找不到行政區: {request.district_name}"
            )
        
        # 使用帶驗證碼重試的查詢
        result = crawler.query_with_captcha_retry(
            area_code=area_code,
            start_date=request.start_date,
            end_date=request.end_date,
            register_kind=request.register_kind
        )
        
        execution_time = time.time() - start_time
        
        records = [
            HouseholdRecord(
                address=item.get("address", ""),
                date=item.get("date", ""),
                type=item.get("type", ""),
                district=request.district_name
            )
            for item in result.data
        ] if result.data else []
        
        return DistrictQueryResponse(
            success=result.success,
            district_name=request.district_name,
            total_count=result.total_count,
            data=records,
            execution_time=round(execution_time, 2),
            error_message=result.error_message if not result.success else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 取得支援的行政區列表
# ============================================================

@app.get(
    "/api/v1/districts",
    tags=["資訊"],
    summary="取得支援的行政區列表"
)
def get_districts():
    """
    取得目前支援查詢的所有行政區及其代碼
    """
    return {
        "city_name": "台北市",
        "city_code": "63000000",
        "districts": HouseholdCrawler.TAIPEI_DISTRICTS
    }


# ============================================================
# 取得編釘類別列表
# ============================================================

@app.get(
    "/api/v1/register-kinds",
    tags=["資訊"],
    summary="取得編釘類別列表"
)
def get_register_kinds():
    """
    取得所有支援的編釘類別
    """
    return {
        "register_kinds": {
            "1": "門牌初編",
            "2": "門牌改編",
            "3": "門牌廢止",
            "4": "門牌復用"
        }
    }


# ============================================================
# 根路徑
# ============================================================

@app.get("/", tags=["系統"])
def root():
    """
    API 根路徑，顯示基本資訊
    """
    return {
        "name": "戶政門牌資料爬蟲 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# ============================================================
# 啟動入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
