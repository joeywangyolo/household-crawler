"""
測試戶政司 API 是否可用 - 使用 Session 維持 CSRF Token
"""
import requests
import re

# API 端點
BASE_URL = "https://www.ris.gov.tw"
QUERY_API = f"{BASE_URL}/info-doorplate/app/doorplate/query"
MAP_API = f"{BASE_URL}/info-doorplate/app/doorplate/map"
MAIN_PAGE = f"{BASE_URL}/info-doorplate/app/doorplate/main"

# 模擬瀏覽器的 Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

def test_with_session():
    """使用 Session 維持 cookies 和 CSRF token"""
    print("=" * 60)
    print("使用 Session 測試 API (維持 CSRF Token)")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Step 1: 訪問主頁面取得 session 和 CSRF token
    print("\n[Step 1] 訪問主頁面...")
    try:
        response = session.get(MAIN_PAGE, timeout=15)
        print(f"狀態碼: {response.status_code}")
        print(f"Cookies: {dict(session.cookies)}")
        
        html = response.text
        
        # 提取 CSRF token
        csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"✓ 找到 CSRF Token: {csrf_token[:50]}...")
        else:
            # 嘗試其他格式
            csrf_match = re.search(r'_csrf["\s:=]+([a-zA-Z0-9\-_]+)', html)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"✓ 找到 CSRF Token (備用): {csrf_token[:50]}...")
            else:
                csrf_token = None
                print("✗ 未找到 CSRF Token")
        
        # 分析頁面結構
        print("\n[頁面分析]")
        
        # 找表單
        forms = re.findall(r'<form[^>]*>', html, re.IGNORECASE)
        print(f"表單數量: {len(forms)}")
        for i, form in enumerate(forms):
            print(f"  表單 {i+1}: {form[:100]}...")
        
        # 找所有 input
        inputs = re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', html, re.IGNORECASE)
        print(f"Input 欄位: {inputs}")
        
        # 找 select
        selects = re.findall(r'<select[^>]*id=["\']([^"\']*)["\']', html, re.IGNORECASE)
        print(f"Select 欄位: {selects}")
        
        # 找 JavaScript 中的 API 呼叫
        js_urls = re.findall(r'(?:url|action)\s*[:=]\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        print(f"JS/表單 URL: {[u for u in js_urls if 'doorplate' in u.lower()]}")
        
        # 找驗證碼
        if "captcha" in html.lower() or "驗證碼" in html:
            captcha_urls = re.findall(r'["\']([^"\']*(?:captcha|verify)[^"\']*)["\']', html, re.IGNORECASE)
            print(f"⚠ 驗證碼相關: {captcha_urls}")
        else:
            print("✓ 頁面中未發現驗證碼")
            
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        return
    
    # Step 2: 模擬點擊「以編釘日期、編釘類別查詢」按鈕
    print("\n" + "-" * 60)
    print("[Step 2] 模擬點擊「以編釘日期、編釘類別查詢」...")
    
    if csrf_token:
        # 準備查詢參數 - 模擬 JS 提交
        query_params = {
            "_csrf": csrf_token,
            "searchType": "date",  # 以編釘日期、編釘類別查詢
        }
        
        try:
            response = session.post(MAP_API, data=query_params, timeout=15)
            print(f"狀態碼: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"內容長度: {len(response.text)} 字元")
            
            # 儲存 map 頁面
            with open("map_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✓ 已儲存 map_page.html")
            
            map_html = response.text
            
            # 分析 map 頁面結構
            print("\n[Map 頁面分析]")
            
            # 找新的 CSRF token
            new_csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', map_html)
            if new_csrf:
                csrf_token = new_csrf.group(1)
                print(f"✓ 新 CSRF Token: {csrf_token[:30]}...")
            
            # 找表單
            forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', map_html, re.IGNORECASE)
            print(f"表單 action: {forms}")
            
            # 找 select 下拉選單
            selects = re.findall(r'<select[^>]*id=["\']([^"\']*)["\']', map_html, re.IGNORECASE)
            print(f"Select 欄位: {selects}")
            
            # 找 input
            inputs = re.findall(r'<input[^>]*(?:name|id)=["\']([^"\']*)["\']', map_html, re.IGNORECASE)
            print(f"Input 欄位: {[i for i in inputs if not i.startswith('_')]}")
            
            # 找 AJAX URL
            ajax_urls = re.findall(r'url\s*:\s*["\']([^"\']+)["\']', map_html, re.IGNORECASE)
            print(f"AJAX URL: {ajax_urls}")
            
            # 找縣市選項 (從 area 標籤)
            city_areas = re.findall(r'data-id="(\d+)"[^>]*alt="([^"]+)"', map_html)
            if city_areas:
                print(f"縣市代碼: {city_areas[:3]}...")
                
        except Exception as e:
            print(f"✗ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return session
    
    # Step 3: 提交查詢 - 選擇台北市
    print("\n" + "-" * 60)
    print("[Step 3] 提交查詢 (台北市, 以編釘日期查詢)...")
    
    if csrf_token:
        query_params = {
            "_csrf": csrf_token,
            "searchType": "date",
            "cityCode": "63000000",  # 台北市
        }
        
        try:
            response = session.post(QUERY_API, data=query_params, timeout=15)
            print(f"狀態碼: {response.status_code}")
            print(f"內容長度: {len(response.text)} 字元")
            
            # 儲存查詢結果頁面
            with open("query_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✓ 已儲存 query_page.html")
            
            query_html = response.text
            
            # 分析查詢頁面
            print("\n[Query 頁面分析]")
            
            # 找新的 CSRF token
            new_csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', query_html)
            if new_csrf:
                csrf_token = new_csrf.group(1)
                print(f"✓ 新 CSRF Token: {csrf_token[:30]}...")
            
            # 找表單
            forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', query_html, re.IGNORECASE)
            print(f"表單 action: {forms}")
            
            # 找 select 下拉選單
            selects = re.findall(r'<select[^>]*id=["\']([^"\']*)["\']', query_html, re.IGNORECASE)
            print(f"Select 欄位: {selects}")
            
            # 找 input
            inputs = re.findall(r'<input[^>]*(?:name|id)=["\']([^"\']*)["\']', query_html, re.IGNORECASE)
            print(f"Input 欄位: {[i for i in inputs if i and not i.startswith('_')]}")
            
            # 找 AJAX URL
            ajax_urls = re.findall(r'url\s*:\s*["\']([^"\']+)["\']', query_html, re.IGNORECASE)
            print(f"AJAX URL: {ajax_urls}")
            
            # 找區域選項
            town_options = re.findall(r'<option[^>]*value=["\']([^"\']+)["\'][^>]*>([^<]+)</option>', query_html)
            if town_options:
                print(f"區域選項: {town_options[:10]}")
            
            # 找編訂類別
            type_options = re.findall(r'type[^>]*value=["\']([^"\']+)["\']', query_html, re.IGNORECASE)
            print(f"編訂類別: {type_options[:5]}")
                
        except Exception as e:
            print(f"✗ 錯誤: {e}")
            import traceback
            traceback.print_exc()

    return session

def save_page_for_analysis(session=None):
    """儲存完整頁面以便分析"""
    print("\n" + "=" * 60)
    print("儲存頁面內容以便分析")
    print("=" * 60)
    
    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
    
    try:
        response = session.get(MAIN_PAGE, timeout=15)
        
        # 儲存 HTML
        with open("page_analysis.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✓ 已儲存 page_analysis.html")
        
        # 提取並顯示所有 JavaScript
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL | re.IGNORECASE)
        inline_scripts = [s for s in scripts if s.strip() and len(s.strip()) > 50]
        
        if inline_scripts:
            with open("page_scripts.js", "w", encoding="utf-8") as f:
                for i, script in enumerate(inline_scripts):
                    f.write(f"// === Script {i+1} ===\n")
                    f.write(script.strip())
                    f.write("\n\n")
            print(f"✓ 已儲存 {len(inline_scripts)} 個內嵌腳本到 page_scripts.js")
            
    except Exception as e:
        print(f"✗ 錯誤: {e}")

if __name__ == "__main__":
    print("戶政司 API 測試 (Session 模式)")
    print("目標網站: https://www.ris.gov.tw/app/portal/3053")
    print("iframe URL: " + MAIN_PAGE)
    print()
    
    session = test_with_session()
    save_page_for_analysis(session)
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
