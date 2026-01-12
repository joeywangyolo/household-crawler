"""
戶政司門牌查詢爬蟲
支援人工輸入驗證碼，未來可擴展為 API 服務
"""
import requests
import re
import base64
import os
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class RegisterKind(Enum):
    """編訂類別"""
    ALL = "0"           # 全部
    INITIAL = "1"       # 門牌初編
    MODIFY = "2"        # 門牌改編
    ADD = "3"           # 門牌增編
    MERGE = "4"         # 門牌合併
    ABOLISH = "5"       # 門牌廢止
    AREA_ADJUST = "6"   # 行政區域調整
    REORGANIZE = "7"    # 門牌整編


@dataclass
class CaptchaInfo:
    """驗證碼資訊"""
    key: str                    # 驗證碼 key
    image_base64: str           # Base64 編碼的圖片
    image_bytes: bytes          # 原始圖片 bytes
    
    def save_image(self, path: str = "captcha.png"):
        """儲存驗證碼圖片"""
        with open(path, "wb") as f:
            f.write(self.image_bytes)
        return path


@dataclass 
class QueryParams:
    """查詢參數"""
    city_code: str              # 縣市代碼 (如 63000000 = 台北市)
    area_code: str              # 區域代碼 (如 63000010 = 松山區)
    start_date: str             # 起始日期 (民國年格式，如 114/09/01)
    end_date: str               # 結束日期 (民國年格式，如 114/11/30)
    register_kind: str = "0"    # 編訂類別，預設全部
    village: str = ""           # 村里
    neighbor: str = ""          # 鄰
    include_no_date: bool = False  # 含未記載編釘日期資料


@dataclass
class QueryResult:
    """查詢結果"""
    success: bool
    data: List[Dict[str, Any]]
    total_count: int
    error_message: Optional[str] = None
    token: Optional[str] = None  # 用於分頁查詢


class HouseholdCrawler:
    """戶政司門牌查詢爬蟲"""
    
    BASE_URL = "https://www.ris.gov.tw"
    MAIN_PAGE = "/info-doorplate/app/doorplate/main"
    MAP_API = "/info-doorplate/app/doorplate/map"
    QUERY_API = "/info-doorplate/app/doorplate/query"
    INQUIRY_API = "/info-doorplate/app/doorplate/inquiry/date"
    CAPTCHA_API = "/info-doorplate/captcha/"
    
    # 台北市各區代碼
    TAIPEI_DISTRICTS = {
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
        "北投區": "63000120",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })
        self.csrf_token: Optional[str] = None
        self.captcha_key: Optional[str] = None
        self._initialized = False
        
    def _get_url(self, path: str) -> str:
        return f"{self.BASE_URL}{path}"
    
    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """從 HTML 提取 CSRF token"""
        match = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
        if match:
            return match.group(1)
        match = re.search(r'content="([^"]+)"[^>]*name="_csrf"', html)
        if match:
            return match.group(1)
        return None
    
    def _extract_captcha_key(self, html: str) -> Optional[str]:
        """從 HTML 提取驗證碼 key"""
        match = re.search(r'id="captchaKey_captchaKey"\s+value="([^"]+)"', html)
        if match:
            return match.group(1)
        return None
    
    def initialize(self) -> bool:
        """
        初始化爬蟲：訪問主頁面 -> 地圖頁面 -> 查詢頁面
        取得必要的 session 和 CSRF token
        """
        try:
            # Step 1: 訪問主頁面
            resp = self.session.get(self._get_url(self.MAIN_PAGE), timeout=15)
            resp.raise_for_status()
            self.csrf_token = self._extract_csrf_token(resp.text)
            
            if not self.csrf_token:
                raise Exception("無法取得 CSRF token")
            
            # Step 2: 選擇「以編釘日期、編釘類別查詢」
            resp = self.session.post(
                self._get_url(self.MAP_API),
                data={"_csrf": self.csrf_token, "searchType": "date"},
                timeout=15
            )
            resp.raise_for_status()
            self.csrf_token = self._extract_csrf_token(resp.text)
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"初始化失敗: {e}")
            return False
    
    def select_city(self, city_code: str = "63000000") -> bool:
        """
        選擇縣市，進入查詢頁面
        city_code: 縣市代碼，預設台北市 (63000000)
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            resp = self.session.post(
                self._get_url(self.QUERY_API),
                data={
                    "_csrf": self.csrf_token,
                    "searchType": "date",
                    "cityCode": city_code
                },
                timeout=15
            )
            resp.raise_for_status()
            
            self.csrf_token = self._extract_csrf_token(resp.text)
            self.captcha_key = self._extract_captcha_key(resp.text)
            
            return True
            
        except Exception as e:
            print(f"選擇縣市失敗: {e}")
            return False
    
    def get_captcha(self) -> Optional[CaptchaInfo]:
        """
        取得驗證碼圖片
        返回 CaptchaInfo 物件，包含圖片和 key
        
        注意：每次呼叫此方法都會產生新的驗證碼！
        取得後必須立即使用，不能重複呼叫。
        """
        if not self.captcha_key:
            print("請先呼叫 select_city() 進入查詢頁面")
            return None
        
        try:
            import time
            timestamp = int(time.time() * 1000)
            # 正確的 URL 格式：CAPTCHA_KEY (大寫)
            captcha_url = f"{self._get_url(self.CAPTCHA_API)}image?CAPTCHA_KEY={self.captcha_key}&time={timestamp}"
            
            print(f"[DEBUG] 取得驗證碼: {captcha_url}")
            print(f"[DEBUG] 使用的 captcha_key: {self.captcha_key}")
            
            resp = self.session.get(captcha_url, timeout=15)
            resp.raise_for_status()
            
            image_bytes = resp.content
            print(f"[DEBUG] 驗證碼圖片大小: {len(image_bytes)} bytes")
            
            if len(image_bytes) < 100:
                print(f"驗證碼圖片內容異常: {len(image_bytes)} bytes")
                return None
                
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # 儲存當前使用的 key
            current_key = self.captcha_key
            
            return CaptchaInfo(
                key=current_key,
                image_base64=image_base64,
                image_bytes=image_bytes
            )
            
        except Exception as e:
            print(f"取得驗證碼失敗: {e}")
            return None
    
    def refresh_captcha(self) -> Optional[CaptchaInfo]:
        """重新產生驗證碼 - 直接取得新圖片即可"""
        # 驗證碼圖片會根據時間戳自動更新，直接取得新的即可
        return self.get_captcha()
    
    def query(self, params: QueryParams, captcha_input: str) -> QueryResult:
        """
        執行查詢
        params: 查詢參數
        captcha_input: 用戶輸入的驗證碼
        """
        if not self.csrf_token or not self.captcha_key:
            return QueryResult(
                success=False,
                data=[],
                total_count=0,
                error_message="請先初始化並取得驗證碼"
            )
        
        try:
            # 準備查詢參數
            post_data = {
                "_csrf": self.csrf_token,
                "searchType": "date",
                "cityCode": params.city_code,
                "areaCode": params.area_code,
                "sDate": params.start_date,
                "eDate": params.end_date,
                "registerKind": params.register_kind,
                "village": params.village,
                "neighbor": params.neighbor,
                "includeNoDate": "true" if params.include_no_date else "",
                "captchaInput": captcha_input,
                "captchaKey": self.captcha_key,
                "tkt": "-1",
            }
            
            # 發送 AJAX 查詢
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRF-TOKEN": self.csrf_token,
            }
            
            print(f"\n[DEBUG] 發送請求到: {self._get_url(self.INQUIRY_API)}")
            print(f"[DEBUG] POST 資料: {post_data}")
            
            resp = self.session.post(
                self._get_url(self.INQUIRY_API),
                data=post_data,
                headers=headers,
                timeout=30
            )
            
            print(f"[DEBUG] 回應狀態: {resp.status_code}")
            print(f"[DEBUG] 回應內容: {resp.text[:500]}")
            
            resp.raise_for_status()
            
            # 解析回應
            result = resp.json()
            print(f"[DEBUG] JSON 結果: {result}")
            
            # 檢查是否有錯誤訊息
            if "errorMsg" in result and result["errorMsg"]:
                try:
                    error_info = __import__('json').loads(result["errorMsg"])
                    if error_info.get("error"):
                        # 驗證碼錯誤，更新 captcha key
                        if "captcha" in error_info:
                            self.captcha_key = error_info["captcha"]
                        return QueryResult(
                            success=False,
                            data=[],
                            total_count=0,
                            error_message=error_info.get("msg", "查詢失敗")
                        )
                except:
                    pass
            
            # 更新 token (用於分頁)
            token = result.get("tkt") or result.get("token")
            
            # 更新 captcha key (如果有新的)
            if "captcha" in result:
                self.captcha_key = result["captcha"]
            
            # 提取資料
            rows = result.get("rows", [])
            total = result.get("records", len(rows))
            
            return QueryResult(
                success=True,
                data=rows,
                total_count=total,
                token=token
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                data=[],
                total_count=0,
                error_message=str(e)
            )


def interactive_query():
    """互動式查詢 - 用於測試"""
    crawler = HouseholdCrawler()
    
    print("=" * 60)
    print("戶政司門牌查詢爬蟲 - 互動模式")
    print("=" * 60)
    
    # 初始化
    print("\n[1/4] 初始化中...")
    if not crawler.initialize():
        print("初始化失敗！")
        return
    print("✓ 初始化成功")
    
    # 選擇縣市 (預設台北市)
    print("\n[2/4] 選擇縣市: 台北市...")
    if not crawler.select_city("63000000"):
        print("選擇縣市失敗！")
        return
    print("✓ 已進入查詢頁面")
    
    # 取得驗證碼
    print("\n[3/4] 取得驗證碼...")
    captcha = crawler.get_captcha()
    if not captcha:
        print("取得驗證碼失敗！")
        return
    
    # 儲存並顯示驗證碼
    captcha_path = captcha.save_image("captcha.png")
    print(f"✓ 驗證碼已儲存到: {captcha_path}")
    print(f"  驗證碼 Key: {captcha.key}")
    
    # 嘗試開啟圖片
    try:
        os.startfile(captcha_path)  # Windows
    except:
        print(f"  請手動開啟 {captcha_path} 查看驗證碼")
    
    # 等待用戶輸入驗證碼
    print("\n" + "-" * 60)
    captcha_input = input("請輸入驗證碼 (輸入 'r' 重新產生): ").strip()
    
    while captcha_input.lower() == 'r':
        print("重新產生驗證碼...")
        captcha = crawler.refresh_captcha()
        if captcha:
            captcha.save_image("captcha.png")
            try:
                os.startfile(captcha_path)
            except:
                pass
        captcha_input = input("請輸入驗證碼 (輸入 'r' 重新產生): ").strip()
    
    # 執行查詢
    print("\n[4/4] 執行查詢...")
    print("  查詢條件:")
    print("  - 縣市: 台北市")
    print("  - 區域: 松山區")
    print("  - 日期: 114/09/01 ~ 114/11/30")
    print("  - 類別: 門牌初編")
    
    params = QueryParams(
        city_code="63000000",
        area_code="63000010",  # 松山區
        start_date="114/09/01",
        end_date="114/11/30",
        register_kind="1",  # 門牌初編
    )
    
    result = crawler.query(params, captcha_input)
    
    print("\n" + "=" * 60)
    print("查詢結果")
    print("=" * 60)
    
    if result.success:
        print(f"✓ 查詢成功！共 {result.total_count} 筆資料")
        if result.data:
            print("\n資料內容:")
            for i, row in enumerate(result.data[:10], 1):  # 只顯示前10筆
                print(f"\n[{i}]")
                for key, value in row.items():
                    print(f"  {key}: {value}")
            if len(result.data) > 10:
                print(f"\n... 還有 {len(result.data) - 10} 筆資料")
        else:
            print("查無資料")
    else:
        print(f"✗ 查詢失敗: {result.error_message}")
        
        # 如果是驗證碼錯誤，提示重試
        if "驗證" in (result.error_message or ""):
            print("\n提示: 驗證碼可能輸入錯誤，請重新執行程式")


if __name__ == "__main__":
    interactive_query()
