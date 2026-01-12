"""
分析網站請求流程 - 教學版
展示如何從瀏覽器 F12 Network 中找到 API 和參數
"""
import requests
import re
import json

BASE_URL = "https://www.ris.gov.tw"

print("=" * 80)
print("網站請求流程分析教學")
print("=" * 80)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
})

# ============================================================================
# Step 1: 訪問主頁面
# ============================================================================
print("\n[Step 1] 訪問主頁面")
print(f"URL: {BASE_URL}/info-doorplate/app/doorplate/main")
print("方法: GET")

resp = session.get(f"{BASE_URL}/info-doorplate/app/doorplate/main", timeout=15)

print(f"狀態碼: {resp.status_code}")
print(f"回應長度: {len(resp.text)} 字元")

# 儲存 HTML
with open("step1_main_page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("✓ 已儲存: step1_main_page.html")

# 提取 CSRF token
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
if csrf:
    csrf_token = csrf.group(1)
    print(f"\n找到隱藏欄位:")
    print(f"  _csrf = {csrf_token[:30]}...")
    print(f"  (這個值會用在後續的 POST 請求中)")

# ============================================================================
# Step 2: 點擊「以編釘日期查詢」
# ============================================================================
print("\n" + "=" * 80)
print("[Step 2] 模擬點擊「以編釘日期、編釘類別查詢」")
print(f"URL: {BASE_URL}/info-doorplate/app/doorplate/map")
print("方法: POST")
print("參數: {")
print(f'  "_csrf": "{csrf_token[:30]}...",')
print('  "searchType": "date"')
print("}")

resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/map",
    data={"_csrf": csrf_token, "searchType": "date"},
    timeout=15
)

print(f"\n狀態碼: {resp.status_code}")
print(f"回應長度: {len(resp.text)} 字元")

with open("step2_map_page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("✓ 已儲存: step2_map_page.html")

# 更新 CSRF token
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
if csrf:
    csrf_token = csrf.group(1)
    print(f"\n新的 _csrf token: {csrf_token[:30]}...")

# ============================================================================
# Step 3: 點擊「台北市」
# ============================================================================
print("\n" + "=" * 80)
print("[Step 3] 模擬點擊地圖上的「台北市」")
print(f"URL: {BASE_URL}/info-doorplate/app/doorplate/query")
print("方法: POST")
print("參數: {")
print(f'  "_csrf": "{csrf_token[:30]}...",')
print('  "searchType": "date",')
print('  "cityCode": "63000000"  # 台北市代碼')
print("}")

resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/query",
    data={"_csrf": csrf_token, "searchType": "date", "cityCode": "63000000"},
    timeout=15
)

print(f"\n狀態碼: {resp.status_code}")
print(f"回應長度: {len(resp.text)} 字元")

with open("step3_query_page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("✓ 已儲存: step3_query_page.html")

# 提取關鍵資訊
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
captcha_key = re.search(r'id="captchaKey_captchaKey"\s+value="([^"]+)"', resp.text)

if csrf and captcha_key:
    print(f"\n找到隱藏欄位:")
    print(f"  _csrf = {csrf.group(1)[:30]}...")
    print(f"  captchaKey = {captcha_key.group(1)}")

# 找出所有 select 選項
print("\n找到的下拉選單:")
selects = re.findall(r'<select[^>]*id="([^"]+)"', resp.text)
for sel in selects[:5]:
    print(f"  - {sel}")

# ============================================================================
# 分析 JavaScript 中的 API 端點
# ============================================================================
print("\n" + "=" * 80)
print("[分析] 從 JavaScript 中找到的 API 端點:")

# 找出所有 URL
urls = re.findall(r'url\s*:\s*["\']([^"\']+)["\']', resp.text)
ajax_urls = [u for u in urls if 'doorplate' in u or 'inquiry' in u]

for url in set(ajax_urls):
    print(f"  - {url}")

print("\n重點: /info-doorplate/app/doorplate/inquiry/date")
print("      ↑ 這就是實際取得資料的 API！")

# ============================================================================
# 總結
# ============================================================================
print("\n" + "=" * 80)
print("總結：如何在 F12 中看到這些資訊")
print("=" * 80)

print("""
1. 打開網站 https://www.ris.gov.tw/app/portal/3053
2. 按 F12 開啟開發者工具
3. 切換到 "Network" 標籤
4. 勾選 "Preserve log"（保留日誌）
5. 開始操作網站：
   - 點擊「以編釘日期、編釘類別查詢」
   - 點擊「台北市」
   - 填寫表單並搜尋

6. 在 Network 列表中找到這些請求：
   ┌─────────────────────────────────────────┐
   │ Name                    │ Type │ Status │
   ├─────────────────────────────────────────┤
   │ map                     │ xhr  │ 200    │  ← Step 2
   │ query                   │ xhr  │ 200    │  ← Step 3
   │ date                    │ xhr  │ 200    │  ← 資料 API！
   └─────────────────────────────────────────┘

7. 點擊 "date" 這個請求，會看到右側面板有多個標籤：
   - Headers: 請求標頭
   - Payload: POST 參數（重要！）
   - Response: 伺服器回應（JSON 資料！）
   - Preview: 格式化的預覽

提示：
- 如果看不到 Payload，可能叫 "Request" 或在 Headers 下方的 "Form Data"
- Response 標籤會顯示原始 JSON
- Preview 標籤會以樹狀結構顯示，更容易閱讀
""")

print("\n已產生以下檔案供分析:")
print("  - step1_main_page.html    (主頁面)")
print("  - step2_map_page.html     (地圖選擇頁)")
print("  - step3_query_page.html   (查詢表單頁)")
print("\n你可以用文字編輯器打開這些檔案，搜尋關鍵字:")
print("  - '_csrf' 找 CSRF token")
print("  - 'captcha' 找驗證碼相關")
print("  - 'url:' 找 JavaScript 中的 API 端點")
