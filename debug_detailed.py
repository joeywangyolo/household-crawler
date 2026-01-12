"""
詳細調試 - 對比瀏覽器和 requests 的請求
"""
import requests
import re
import time
import json

BASE_URL = "https://www.ris.gov.tw"

session = requests.Session()

# 模擬更完整的瀏覽器 headers
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})

print("=" * 60)
print("詳細調試 - requests 驗證碼問題")
print("=" * 60)

# Step 1: 訪問主頁面
print("\n[1] 訪問主頁面...")
resp = session.get(f"{BASE_URL}/info-doorplate/app/doorplate/main", timeout=15)
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
print(f"  CSRF: {csrf[:20]}...")
print(f"  Cookies: {dict(session.cookies)}")

# Step 2: 進入 map 頁面
print("\n[2] 進入 map 頁面...")
resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/map",
    data={"_csrf": csrf, "searchType": "date"},
    timeout=15
)
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)

# Step 3: 進入 query 頁面
print("\n[3] 進入 query 頁面 (台北市)...")
resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/query",
    data={"_csrf": csrf, "searchType": "date", "cityCode": "63000000"},
    timeout=15
)

csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
captcha_key = re.search(r'id="captchaKey_captchaKey"\s+value="([^"]+)"', resp.text).group(1)

print(f"  CSRF: {csrf[:20]}...")
print(f"  Captcha Key: {captcha_key}")
print(f"  Cookies: {dict(session.cookies)}")

# Step 4: 獲取驗證碼 - 不加 timestamp 試試
print("\n[4] 獲取驗證碼...")

# 方法 1: 不帶 timestamp
captcha_url_1 = f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={captcha_key}"
resp1 = session.get(captcha_url_1, timeout=15)
print(f"  方法1 (無timestamp): {len(resp1.content)} bytes")
with open("debug_captcha_1.png", "wb") as f:
    f.write(resp1.content)

# 方法 2: 帶 timestamp
timestamp = int(time.time() * 1000)
captcha_url_2 = f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={captcha_key}&time={timestamp}"
resp2 = session.get(captcha_url_2, timeout=15)
print(f"  方法2 (有timestamp): {len(resp2.content)} bytes")
with open("debug_captcha_2.png", "wb") as f:
    f.write(resp2.content)

print("\n  已儲存 debug_captcha_1.png 和 debug_captcha_2.png")
print("  請查看兩張圖片是否相同")

import os
try:
    os.startfile("debug_captcha_1.png")
except:
    pass

# 等待用戶輸入
print("\n" + "-" * 60)
captcha_input = input("請輸入 debug_captcha_1.png 中的驗證碼: ").strip()

# Step 5: 測試查詢 - 詳細顯示請求內容
print("\n[5] 測試查詢...")

post_data = {
    "_csrf": csrf,
    "searchType": "date",
    "cityCode": "63000000",
    "areaCode": "63000010",  # 松山區
    "village": "",
    "neighbor": "",
    "sDate": "114/09/01",
    "eDate": "114/11/30",
    "registerKind": "1",
    "includeNoDate": "",
    "captchaInput": captcha_input,
    "captchaKey": captcha_key,
    "tkt": "-1",
}

print("\n  POST 資料:")
for k, v in post_data.items():
    print(f"    {k}: {v[:30] if len(str(v)) > 30 else v}")

# 使用更完整的 headers
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "X-CSRF-TOKEN": csrf,
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/info-doorplate/app/doorplate/query",
}

print("\n  請求 Headers:")
for k, v in headers.items():
    print(f"    {k}: {v[:50] if len(str(v)) > 50 else v}")

resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
    data=post_data,
    headers=headers,
    timeout=30
)

print(f"\n  回應狀態: {resp.status_code}")
print(f"  回應 Headers: {dict(resp.headers)}")

try:
    result = resp.json()
    print(f"\n  JSON 結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result.get("errorMsg"):
        error = json.loads(result["errorMsg"])
        print(f"\n  ❌ 錯誤: {error.get('msg')}")
        
        if "captcha" in error:
            new_key = error["captcha"]
            print(f"  新 Captcha Key: {new_key}")
            
            # 用新 key 獲取驗證碼再試一次
            print("\n[6] 使用新的 Captcha Key 重試...")
            
            captcha_url = f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={new_key}"
            resp = session.get(captcha_url, timeout=15)
            with open("debug_captcha_new.png", "wb") as f:
                f.write(resp.content)
            print(f"  已儲存 debug_captcha_new.png ({len(resp.content)} bytes)")
            
            try:
                os.startfile("debug_captcha_new.png")
            except:
                pass
            
            captcha_input = input("請輸入新驗證碼: ").strip()
            
            # 更新 captcha key
            post_data["captchaKey"] = new_key
            post_data["captchaInput"] = captcha_input
            headers["X-CSRF-TOKEN"] = csrf
            
            resp = session.post(
                f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
                data=post_data,
                headers=headers,
                timeout=30
            )
            
            result = resp.json()
            print(f"\n  重試結果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n  ✓ 成功！找到 {result.get('records', 0)} 筆資料")
        if result.get("rows"):
            print(f"  第一筆: {result['rows'][0]}")
            
except Exception as e:
    print(f"\n  解析錯誤: {e}")
    print(f"  原始回應: {resp.text[:500]}")

print("\n" + "=" * 60)
print("測試完成")
