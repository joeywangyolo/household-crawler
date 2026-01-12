"""
調試查詢 API - 找出正確的請求格式
"""
import requests
import re
import time

BASE_URL = "https://www.ris.gov.tw"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

print("=" * 60)
print("調試查詢 API")
print("=" * 60)

# Step 1: 訪問主頁面
print("\n[1] 訪問主頁面...")
resp = session.get(f"{BASE_URL}/info-doorplate/app/doorplate/main", timeout=15)
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
print(f"  CSRF: {csrf[:20]}...")

# Step 2: 進入 map 頁面
print("\n[2] 進入 map 頁面...")
resp = session.post(f"{BASE_URL}/info-doorplate/app/doorplate/map", 
                    data={"_csrf": csrf, "searchType": "date"}, timeout=15)
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)

# Step 3: 進入 query 頁面
print("\n[3] 進入 query 頁面 (台北市)...")
resp = session.post(f"{BASE_URL}/info-doorplate/app/doorplate/query",
                    data={"_csrf": csrf, "searchType": "date", "cityCode": "63000000"}, timeout=15)

csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
captcha_key = re.search(r'id="captchaKey_captchaKey"\s+value="([^"]+)"', resp.text).group(1)

print(f"  CSRF: {csrf[:20]}...")
print(f"  Captcha Key: {captcha_key}")

# 取得並儲存驗證碼
print("\n[4] 取得驗證碼...")
timestamp = int(time.time() * 1000)
captcha_url = f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={captcha_key}&time={timestamp}"
captcha_resp = session.get(captcha_url, timeout=15)
with open("debug_captcha.png", "wb") as f:
    f.write(captcha_resp.content)
print(f"  已儲存 debug_captcha.png ({len(captcha_resp.content)} bytes)")

# 打開圖片
import os
try:
    os.startfile("debug_captcha.png")
except:
    pass

# 等待用戶輸入
print("\n" + "-" * 60)
captcha_input = input("請輸入驗證碼: ").strip()

# Step 5: 測試不同的日期格式
print("\n[5] 測試查詢...")

# 從網頁 JS 分析，日期格式應該是民國年
date_formats = [
    ("114/09/01", "114/11/30"),  # 民國年/月/日
    ("1140901", "1141130"),       # 民國年月日 (無分隔)
    ("114-09-01", "114-11-30"),   # 民國年-月-日
]

for sDate, eDate in date_formats:
    print(f"\n  測試日期格式: {sDate} ~ {eDate}")
    
    post_data = {
        "_csrf": csrf,
        "searchType": "date",
        "cityCode": "63000000",
        "areaCode": "63000010",  # 松山區
        "village": "",
        "neighbor": "",
        "sDate": sDate,
        "eDate": eDate,
        "registerKind": "1",  # 門牌初編
        "includeNoDate": "",
        "captchaInput": captcha_input,
        "captchaKey": captcha_key,
        "tkt": "-1",
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRF-TOKEN": csrf,
        "Referer": f"{BASE_URL}/info-doorplate/app/doorplate/query",
    }
    
    resp = session.post(
        f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
        data=post_data,
        headers=headers,
        timeout=30
    )
    
    print(f"  狀態: {resp.status_code}")
    
    try:
        result = resp.json()
        print(f"  回應: {result}")
        
        if result.get("records", 0) > 0:
            print(f"\n  ✓ 成功！找到 {result['records']} 筆資料")
            print(f"  資料: {result.get('rows', [])[:2]}")
            break
        elif "errorMsg" in result:
            import json
            error = json.loads(result["errorMsg"])
            print(f"  錯誤: {error.get('msg', result['errorMsg'])}")
            
            # 更新 captcha key
            if "captcha" in error:
                captcha_key = error["captcha"]
                print(f"  新的 Captcha Key: {captcha_key}")
                
                # 取得新驗證碼
                timestamp = int(time.time() * 1000)
                captcha_url = f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={captcha_key}&time={timestamp}"
                captcha_resp = session.get(captcha_url, timeout=15)
                with open("debug_captcha.png", "wb") as f:
                    f.write(captcha_resp.content)
                print(f"  已更新 debug_captcha.png")
                try:
                    os.startfile("debug_captcha.png")
                except:
                    pass
                captcha_input = input("  請輸入新驗證碼: ").strip()
    except Exception as e:
        print(f"  解析錯誤: {e}")
        print(f"  原始回應: {resp.text[:500]}")

print("\n" + "=" * 60)
print("測試完成")
