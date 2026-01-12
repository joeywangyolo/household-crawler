# Postman 測試指南

## 簡介

**是的，你可以在 Postman 中手動執行這些請求來取得資料！**

但需要注意幾個關鍵點：
1. 必須按順序執行（不能跳步）
2. 需要維持 Session（Cookies）
3. CSRF token 會在每次請求後更新

---

## 前置準備

### 1. 安裝 Postman
下載：https://www.postman.com/downloads/

### 2. 設定 Postman
1. Settings → General
2. 確保 "Automatically follow redirects" 開啟
3. 確保 "Enable SSL certificate verification" 開啟

### 3. 建立新的 Collection
1. 點擊左側 "Collections"
2. 點擊 "+" 建立新 Collection
3. 命名為 "戶政司門牌查詢"

---

## 請求流程

### 📋 重要提醒
- **所有請求必須在同一個 Tab 中執行**（保持 Cookies）
- **每個請求的回應都要複製參數給下一個請求**
- **不能跳過任何步驟**

---

## Request 1: 取得初始 Token

### 基本資訊
```
Method: GET
URL: https://www.ris.gov.tw/info-doorplate/app/doorplate/main
```

### Headers
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-TW,zh;q=0.9,en;q=0.8
```

### 執行步驟
1. 點擊 "Send"
2. 查看 Response（Body 標籤）
3. 按 `Ctrl+F` 搜尋 `name="_csrf"`
4. 找到這行：
   ```html
   <input type="hidden" name="_csrf" value="74eeb05b-2e60-4d92-b48b-35e410...">
   ```
5. **複製 value 的值**（整串，包括後面的...）

### 結果
```
✓ 取得 csrf_token_1
```

---

## Request 2: 進入地圖頁面

### 基本資訊
```
Method: POST
URL: https://www.ris.gov.tw/info-doorplate/app/doorplate/map
```

### Headers
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
Content-Type: application/x-www-form-urlencoded
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-TW,zh;q=0.9,en;q=0.8
```

### Body
選擇 `x-www-form-urlencoded`，新增：

| Key | Value |
|-----|-------|
| _csrf | [從 Request 1 複製的值] |
| searchType | date |

### 執行步驟
1. 點擊 "Send"
2. 查看 Response
3. 搜尋 `name="_csrf"`
4. **複製新的 _csrf value**

### 結果
```
✓ 取得 csrf_token_2
```

---

## Request 3: 選擇縣市（台北市）

### 基本資訊
```
Method: POST
URL: https://www.ris.gov.tw/info-doorplate/app/doorplate/query
```

### Headers
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
Content-Type: application/x-www-form-urlencoded
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-TW,zh;q=0.9,en;q=0.8
```

### Body
選擇 `x-www-form-urlencoded`，新增：

| Key | Value |
|-----|-------|
| _csrf | [從 Request 2 複製的值] |
| searchType | date |
| cityCode | 63000000 |

### 執行步驟
1. 點擊 "Send"
2. 查看 Response
3. 搜尋 `name="_csrf"`，**複製新的值**
4. 搜尋 `id="captchaKey_captchaKey"`
5. 找到這行：
   ```html
   <input type="hidden" id="captchaKey_captchaKey" value="ddcae9a4461f49309a4ee8c65099ffc2">
   ```
6. **複製 captchaKey 的 value**

### 結果
```
✓ 取得 csrf_token_3
✓ 取得 captcha_key
```

---

## Request 4: 取得驗證碼圖片

### 基本資訊
```
Method: GET
URL: https://www.ris.gov.tw/info-doorplate/captcha/image?CAPTCHA_KEY=[captcha_key]&time=[timestamp]
```

**注意**：
- `[captcha_key]` 替換成 Request 3 取得的值
- `[timestamp]` 可以用任意數字，例如 `1736226789123`

完整範例：
```
https://www.ris.gov.tw/info-doorplate/captcha/image?CAPTCHA_KEY=ddcae9a4461f49309a4ee8c65099ffc2&time=1736226789123
```

### Headers
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
```

### 執行步驟
1. 點擊 "Send"
2. 點擊 Response 區域右上角的 "Save Response"
3. 選擇 "Save to a file"
4. 儲存為 `captcha.png`
5. 打開圖片，**記下驗證碼內容**（例如：ABC12）

### 結果
```
✓ 取得驗證碼圖片
✓ 手動識別驗證碼
```

---

## Request 5: 查詢資料（最重要！）

### 基本資訊
```
Method: POST
URL: https://www.ris.gov.tw/info-doorplate/app/doorplate/inquiry/date
```

### Headers
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
Accept: application/json, text/javascript, */*; q=0.01
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
X-CSRF-TOKEN: [從 Request 3 複製的 csrf_token_3]
Referer: https://www.ris.gov.tw/info-doorplate/app/doorplate/query
```

**重要**：`X-CSRF-TOKEN` 的值要填入 Request 3 取得的 csrf token

### Body
選擇 `x-www-form-urlencoded`，新增以下 **25 個參數**：

| Key | Value | 說明 |
|-----|-------|------|
| searchType | date | 查詢類型 |
| cityCode | 63000000 | 台北市 |
| tkt | -1 | 固定值 |
| areaCode | 63000010 | 松山區 |
| village | | 空值（留空） |
| neighbor | | 空值（留空） |
| sDate | 114-09-01 | ⚠️ 用破折號！ |
| eDate | 114-11-30 | ⚠️ 用破折號！ |
| _includeNoDate | on | 固定值 |
| registerKind | 1 | 1=初編 |
| captchaInput | [手動輸入] | 驗證碼 |
| captchaKey | [Request 3] | captcha_key |
| _csrf | [Request 3] | csrf_token_3 |
| floor | | 空值（留空） |
| lane | | 空值（留空） |
| alley | | 空值（留空） |
| number | | 空值（留空） |
| number1 | | 空值（留空） |
| ext | | 空值（留空） |
| _search | false | 固定值 |
| nd | 1736226789123 | 時間戳記 |
| rows | 50 | 每頁筆數 |
| page | 1 | 頁碼 |
| sidx | | 空值（留空） |
| sord | asc | 排序方式 |

### 執行步驟
1. 仔細填入所有 25 個參數
2. 確認 `captchaInput` 填入正確的驗證碼
3. 確認 `sDate` 和 `eDate` 使用破折號（-）
4. 點擊 "Send"
5. 查看 Response

### 成功的回應
```json
{
  "errorMsg": "",
  "total": 5,
  "page": 1,
  "records": 246,
  "rows": [
    {
      "v1": "臺北市松山區慈祐里014鄰八德路四段４８６號",
      "v2": "民國114年10月29日",
      "v3": "1"
    },
    ...
  ],
  "tkt": -1,
  "tktFirst": -1,
  "tkTimes": 0
}
```

### 結果
```
✓ 成功取得 246 筆資料！
```

---

## 常見錯誤

### 錯誤 1：驗證碼錯誤
```json
{
  "errorMsg": "{\"title\":\"圖形驗證碼驗證失敗\",\"captcha\":\"xxx\"}"
}
```

**解決方法**：
1. 重新從 Request 3 開始
2. 取得新的 captcha_key
3. 重新下載驗證碼圖片
4. 確認驗證碼大小寫正確

---

### 錯誤 2：CSRF Token 錯誤
```json
{
  "errorMsg": "Invalid CSRF Token"
}
```

**解決方法**：
1. 確認使用的是 Request 3 取得的最新 token
2. 確認 `X-CSRF-TOKEN` header 和 `_csrf` body 參數都有填
3. 重新從 Request 1 開始

---

### 錯誤 3：查無資料
```json
{
  "errorMsg": "{\"title\":\"查無資料\"}",
  "records": 0
}
```

**可能原因**：
1. 日期格式錯誤（必須用破折號 `-`）
2. 區域代碼錯誤
3. 該時間區間真的沒有資料

**解決方法**：
1. 檢查 `sDate` 和 `eDate` 格式：`114-09-01`
2. 嘗試不同的日期區間
3. 嘗試不同的區域

---

### 錯誤 4：參數缺少
```json
{
  "errorMsg": "Missing required parameter"
}
```

**解決方法**：
確認所有 25 個參數都有填入（包括空值參數）

---

## 參數說明

### 縣市代碼（cityCode）
| 縣市 | 代碼 |
|------|------|
| 台北市 | 63000000 |
| 新北市 | 65000000 |
| 桃園市 | 68000000 |
| 台中市 | 66000000 |
| 台南市 | 67000000 |
| 高雄市 | 64000000 |

### 台北市區域代碼（areaCode）
| 區域 | 代碼 |
|------|------|
| 松山區 | 63000010 |
| 信義區 | 63000020 |
| 大安區 | 63000030 |
| 中山區 | 63000040 |
| 中正區 | 63000050 |
| 大同區 | 63000060 |
| 萬華區 | 63000070 |
| 文山區 | 63000080 |
| 南港區 | 63000090 |
| 內湖區 | 63000100 |
| 士林區 | 63000110 |
| 北投區 | 63000120 |

### 編訂類別（registerKind）
| 類別 | 代碼 |
|------|------|
| 全部 | 0 |
| 門牌初編 | 1 |
| 門牌改編 | 2 |
| 門牌增編 | 3 |
| 門牌廢止 | 4 |

---

## 進階技巧

### 1. 使用 Postman 變數
可以建立環境變數來儲存 token：

1. 點擊右上角的齒輪 → Manage Environments
2. 建立新環境 "戶政司"
3. 新增變數：
   - `csrf_token`
   - `captcha_key`

4. 在 Request 中使用：`{{csrf_token}}`

### 2. 使用 Pre-request Script 自動提取
在 Request 2 的 "Tests" 標籤中加入：

```javascript
var html = pm.response.text();
var match = html.match(/name="_csrf"\s+value="([^"]+)"/);
if (match) {
    pm.environment.set("csrf_token", match[1]);
}
```

這樣就會自動提取並儲存 CSRF token。

### 3. 匯出 Collection
完成設定後，可以匯出 Collection 分享給其他人：
1. Collection 右鍵 → Export
2. 選擇 Collection v2.1
3. 儲存為 `.json` 檔案

---

## 總結

### ✅ 優點
- 可視化操作，容易理解流程
- 可以手動測試每個步驟
- 適合除錯和學習

### ❌ 缺點
- 需要手動複製貼上參數
- 驗證碼需要人工識別
- 不適合大量查詢

### 💡 建議
- 用 Postman 理解流程
- 用 Python 腳本自動化

---

**完成！你現在可以用 Postman 手動測試整個 API 流程了。**
