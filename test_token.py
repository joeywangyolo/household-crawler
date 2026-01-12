"""
測試 API 回應是否有 token 欄位
驗證是否可以用同一個 session 連續查詢多個區域
"""
import requests
import re
import time
import json

# Pillow patch
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

try:
    import ddddocr
    ocr = ddddocr.DdddOcr()
    print("[OCR] ddddocr 已載入")
except:
    ocr = None
    print("[OCR] ddddocr 未載入，將使用手動輸入")

BASE_URL = "https://www.ris.gov.tw"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

print("=" * 60)
print("測試 Token 機制")
print("=" * 60)

# Step 1: 初始化
print("\n[1] 初始化 Session...")

#第一層請求 API  
resp = session.get(f"{BASE_URL}/info-doorplate/app/doorplate/main", timeout=15)
csrf_token = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
print(f"第一層 CSRF: {csrf_token}")

#第二層請求 API  
resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/map",
    data={"_csrf": csrf_token, "searchType": "date"},
    timeout=15
)
csrf_token = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
print(f"第二層 CSRF: {csrf_token}")

#第三層請求 API  
resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/query",
    data={"_csrf": csrf_token, "searchType": "date", "cityCode": "63000000"},
    timeout=15
)
csrf_token = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text).group(1)
captcha_key = re.search(r'id="captchaKey_captchaKey"\s+value="([^"]+)"', resp.text).group(1)
print(f"第三層 CSRF: {csrf_token}")
print(f"Captcha Key: {captcha_key}")

# Step 2: 取得驗證碼
print("\n[2] 取得驗證碼...")
ts = int(time.time() * 1000)
#第四層請求 API  
resp = session.get(f"{BASE_URL}/info-doorplate/captcha/image?CAPTCHA_KEY={captcha_key}&time={ts}", timeout=15)
with open("captcha.png", "wb") as f:
    f.write(resp.content)
print("已儲存 captcha.png")

# OCR 或手動輸入
captcha_input = None
if ocr:
    try:
        result = ocr.classification(resp.content)
        if len(result) == 5:
            captcha_input = result.lower()
            print(f"[OCR] 識別結果: {captcha_input}")
    except Exception as e:
        print(f"[OCR] 識別失敗: {e}")

if not captcha_input:
    import os
    try:
        os.startfile("captcha.png")
    except:
        pass
    captcha_input = input("請輸入驗證碼: ").strip()

# Step 3: 第一次查詢（松山區）
print("\n[3] 第一次查詢（松山區）...")

def extract_token_and_captcha_key(result_json: dict):
    """從 errorMsg 裡解析 token / captchaKey（這站把它包在 errorMsg 文字內）"""
    token = None
    new_captcha_key = None

    error_msg = result_json.get("errorMsg")
    if error_msg:
        try:
            error_data = json.loads(error_msg)
            token = error_data.get("token")
            new_captcha_key = error_data.get("captcha")
        except Exception:
            pass

    return token, new_captcha_key


def build_post_data(
    csrf_token: str,
    captcha_key: str,
    captcha_input: str,
    city_code: str,
    area_code: str,
    start_date: str,
    end_date: str,
    register_kind: str,
    page: int,
    token: str = None
)-> dict:
    """產生每一次 request 用的 post_data（動態帶 page / nd / token / captchaInput）"""

    nd = int(time.time() * 1000)
    post_data = {
    "searchType": "date",
    "cityCode": city_code,
    "tkt": "-1",
    "areaCode": area_code,  # 松山區
    "village": "",
    "neighbor": "",
    "sDate": start_date,
    "eDate": end_date,
    "_includeNoDate": "on",
    "registerKind": register_kind,
    "captchaInput": captcha_input,
    "captchaKey": captcha_key,
    "_csrf": csrf_token,
    "floor": "",
    "lane": "",
    "alley": "",
    "number": "",
    "number1": "",
    "ext": "",
    "_search": "false",
    "nd": str(nd),
    "rows": "50",
    "page": str(page),
    "sidx": "",
    "sord": "asc",
    }
    if token:
        post_data["token"] = token
        post_data["captchaInput"] = ""

    return post_data

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "X-CSRF-TOKEN": csrf_token,
    "Referer": f"{BASE_URL}/info-doorplate/app/doorplate/query",
}
# 你這次測試固定查松山區，但已「活化」：改這些參數就能查別區/別日期
city_code = "63000000"
area_code = "63000010"  # 松山區
start_date = "114-09-01"
end_date = "114-11-30"
register_kind = "1"

post_data_page1 = build_post_data(
    csrf_token=csrf_token,
    captcha_key=captcha_key,
    captcha_input=captcha_input,
    city_code=city_code,
    area_code=area_code,
    start_date=start_date,
    end_date=end_date,
    register_kind=register_kind,
    page=1,
    token=None
)
#第五層請求 API  (查詢結果)
resp = session.post(
    f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
    data=post_data_page1,
    headers=headers,
    timeout=30
)

result = resp.json()

print("\n" + "=" * 60)
print("第一次查詢 - 完整 API 回應")
print("=" * 60)
print(json.dumps(result, ensure_ascii=False, indent=2))

# 檢查關鍵欄位
records = result.get("records", 0)
total_pages = int(result.get("total", 1) or 1)  # ✅ dict 正確用法
page = int(result.get("page", 1) or 1)
rows_len = len(result.get("rows", []) or [])
print("\n" + "-" * 60)
print("關鍵欄位檢查:")
print(f"  records: {result.get('records', 'N/A')}")
print(f"  token: {result.get('token', '❌ 不存在')}")
print(f"  tkt: {result.get('tkt', 'N/A')}")
print(f"  tkc: {result.get('tkc', 'N/A')}")
print(f"  errorMsg: {result.get('errorMsg', 'N/A')}")

# 從 errorMsg 中提取 token（關鍵！）
token = None
new_captcha_key = None
if result.get('errorMsg'):
    try:
        error_data = json.loads(result.get('errorMsg'))
        token = error_data.get('token')
        new_captcha_key = error_data.get('captcha')
        print(f"\n從 errorMsg 中提取:")
        print(f"  token: {token[:50] if token else 'N/A'}...")
        print(f"  new captcha key: {new_captcha_key}")
    except:
        pass
# 從 errorMsg 中提取 token / captchaKey（關鍵）
current_token, new_captcha_key = extract_token_and_captcha_key(result)

if new_captcha_key:
    captcha_key = new_captcha_key  # ✅ 更新 captchaKey（站台會換）
if current_token:
    print(f"\n從 errorMsg 中提取:")
    print(f"  token: {current_token[:50]}...")
    print(f"  new captcha key: {captcha_key}")
else:
    print("\n⚠️ 沒拿到 token，後續分頁可能會失敗（通常不會）")
# ---- page 2..N：用 token 分頁 ----
for p in range(2, total_pages + 1):
    post_data_p = build_post_data(
        csrf_token=csrf_token,
        captcha_key=captcha_key,
        captcha_input="",              # ✅ 分頁不用 captcha
        city_code=city_code,
        area_code=area_code,
        start_date=start_date,
        end_date=end_date,
        register_kind=register_kind,
        page=p,
        token=current_token            # ✅ 帶 token
    )

    resp = session.post(
        f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
        data=post_data_p,
        headers=headers,
        timeout=30
    )
    result_p = resp.json()
    # 每頁更新 token/captchaKey（保險）
    token_p, captcha_key_p = extract_token_and_captcha_key(result_p)
    if captcha_key_p:
        captcha_key = captcha_key_p
    if token_p:
        current_token = token_p

    rows_len_p = len(result_p.get("rows", []) or [])
    print(f"[分頁] page {p}/{total_pages} rows_len={rows_len_p} token={'Y' if token_p else 'N'}")
# # 如果有資料，嘗試第二次查詢
# if result.get('records', 0) > 0 and token:
#     print("\n" + "=" * 60)
#     print("[4] 第二次查詢（信義區）- 使用 token，不輸入新驗證碼")
#     print("=" * 60)
    
#     post_data_2 = post_data.copy()
#     post_data_2["areaCode"] = "63000020"  # 信義區
#     post_data_2["nd"] = str(int(time.time() * 1000))
#     post_data_2["token"] = token  # 關鍵：使用 token
    
#     # 使用新的 captcha key（但不需要輸入驗證碼內容）
#     if new_captcha_key:
#         post_data_2["captchaKey"] = new_captcha_key
    
#     # 清空驗證碼輸入（測試是否需要）
#     post_data_2["captchaInput"] = ""
    
#     print(f"使用 token: {token[:50]}...")
    
#     resp2 = session.post(
#         f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
#         data=post_data_2,
#         headers=headers,
#         timeout=30
#     )
    
#     result2 = resp2.json()
    
#     print("\n第二次查詢 - API 回應（簡化）")
#     print(f"  records: {result2.get('records', 0)}")
#     print(f"  errorMsg: {result2.get('errorMsg', 'N/A')}")
    
#     print("\n" + "-" * 60)
#     print("第二次查詢結果:")
#     if result2.get('records', 0) > 0:
#         print(f"  ✅ 成功！找到 {result2.get('records')} 筆資料")
#         print("  → Token 機制有效！可以連續查詢多個區域！")
        
#         # 嘗試第三次查詢
#         print("\n" + "=" * 60)
#         print("[5] 第三次查詢（大安區）- 繼續使用 token")
#         print("=" * 60)
        
#         # 從第二次回應中提取新 token
#         token2 = None
#         if result2.get('errorMsg'):
#             try:
#                 error_data2 = json.loads(result2.get('errorMsg'))
#                 token2 = error_data2.get('token')
#             except:
#                 pass
        
#         post_data_3 = post_data_2.copy()
#         post_data_3["areaCode"] = "63000030"  # 大安區
#         post_data_3["nd"] = str(int(time.time() * 1000))
#         if token2:
#             post_data_3["token"] = token2
        
#         resp3 = session.post(
#             f"{BASE_URL}/info-doorplate/app/doorplate/inquiry/date",
#             data=post_data_3,
#             headers=headers,
#             timeout=30
#         )
        
#         result3 = resp3.json()
#         print(f"  records: {result3.get('records', 0)}")
#         if result3.get('records', 0) > 0:
#             print(f"  ✅ 第三次也成功！")
#         else:
#             print(f"  ❌ 失敗: {result3.get('errorMsg', 'N/A')}")
            
#     elif result2.get('errorMsg'):
#         error = result2.get('errorMsg')
#         try:
#             error = json.loads(error)
#         except:
#             pass
#         print(f"  ❌ 失敗: {error}")
#     else:
#         print(f"  ❓ 未知結果: {result2}")
# else:
#     print("\n❌ 第一次查詢失敗，無法繼續測試")
#     if result.get('errorMsg'):
#         try:
#             error = json.loads(result.get('errorMsg'))
#             print(f"錯誤: {error}")
#         except:
#             print(f"錯誤: {result.get('errorMsg')}")
