"""
取得新的驗證碼圖片用於測試 ddddocr
"""
import requests
import re
import time

BASE_URL = "https://www.ris.gov.tw"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
})

print("取得驗證碼...")

# Step 1-3: 導航到查詢頁面
resp = session.get(f"{BASE_URL}/info-doorplate/app/doorplate/main")
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)

resp = session.post(f"{BASE_URL}/info-doorplate/app/doorplate/map", 
                    data={"_csrf": csrf, "searchType": "date"})
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)

resp = session.post(f"{BASE_URL}/info-doorplate/app/doorplate/query",
                    data={"_csrf": csrf, "searchType": "date", "cityCode": "63000000"})

captcha_key = re.search(r'id="captchaKey_captchaKey"\s+value="([^"]+)"', resp.text).group(1)

# 取得多個驗證碼用於測試
for i in range(5):
    ts = int(time.time() * 1000)
    url = f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={captcha_key}&time={ts}"
    resp = session.get(url)
    
    filename = f"test_captcha_{i}.png"
    with open(filename, "wb") as f:
        f.write(resp.content)
    print(f"✓ 已儲存: {filename} ({len(resp.content)} bytes)")
    time.sleep(0.5)

print("\n完成！已取得 5 個驗證碼圖片")
