# OCR 自動識別驗證碼 - 整合說明

## 目前狀態

### ✅ 已完成
- ddddocr 套件已安裝
- OCR 框架已整合到 `crawler_requests.py`
- 自動降級機制：OCR 失敗時自動切換到手動輸入
- 使用者確認機制：可以選擇是否使用 OCR 識別結果

### ⚠️ 已知問題
**Pillow 版本相容性問題**
- ddddocr 1.0.6 與 Pillow 12.x 不相容
- 錯誤訊息：`module 'PIL.Image' has no attribute 'ANTIALIAS'`
- 原因：Pillow 10.0.0 移除了 `ANTIALIAS` 常數

---

## 使用方式

### 方法 1：使用 OCR（自動識別）

```python
from crawler_requests import HouseholdCrawler

# 啟用 OCR（預設）
crawler = HouseholdCrawler(use_ocr=True)

# 初始化並取得驗證碼
crawler.init_session("63000000")
crawler.get_captcha("captcha.png")

# 自動識別
captcha_text = crawler.recognize_captcha("captcha.png")
if captcha_text:
    print(f"識別結果: {captcha_text}")
else:
    print("識別失敗，請手動輸入")
```

### 方法 2：純手動輸入

```python
# 停用 OCR
crawler = HouseholdCrawler(use_ocr=False)

# 手動輸入驗證碼
captcha_text = input("請輸入驗證碼: ")
```

### 方法 3：互動模式（推薦）

```bash
python crawler_requests.py
```

程式會：
1. 嘗試 OCR 自動識別
2. 顯示識別結果並詢問是否使用
3. 如果拒絕或失敗，則要求手動輸入

---

## 解決 Pillow 相容性問題

### 方案 1：降級 Pillow（不推薦）

由於 Python 3.13 的限制，無法直接降級到 Pillow 9.x。

### 方案 2：等待 ddddocr 更新（推薦）

目前 ddddocr 尚未更新以支援 Pillow 12.x。可以：
- 關注 ddddocr GitHub：https://github.com/sml2h3/ddddocr
- 等待新版本發布

### 方案 3：使用替代 OCR 庫

#### 選項 A：muggle-ocr
```bash
pip install muggle-ocr
```

```python
from muggle_ocr import SDK

sdk = SDK(model_type=SDK.ModelType.Captcha)
with open("captcha.png", "rb") as f:
    result = sdk.predict(image_bytes=f.read())
```

#### 選項 B：easyocr
```bash
pip install easyocr
```

```python
import easyocr

reader = easyocr.Reader(['en'])
result = reader.readtext('captcha.png', detail=0)
```

#### 選項 C：PaddleOCR
```bash
pip install paddleocr
```

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='en')
result = ocr.ocr('captcha.png', cls=True)
```

### 方案 4：修改 ddddocr 原始碼（進階）

手動修改 ddddocr 的 `ANTIALIAS` 引用：

1. 找到 ddddocr 安裝位置：
```bash
python -c "import ddddocr; print(ddddocr.__file__)"
```

2. 編輯檔案，將所有 `Image.ANTIALIAS` 替換為 `Image.LANCZOS`

---

## 當前建議

### 短期方案（目前使用）
**保留手動輸入**
- 優點：穩定可靠，100% 準確
- 缺點：需要人工介入
- 適用：小量查詢、測試階段

### 中期方案
**使用替代 OCR 庫**
- 推薦：muggle-ocr（專為驗證碼設計）
- 優點：與 Pillow 12.x 相容
- 缺點：需要重新整合和測試

### 長期方案
**訓練自定義模型**
- 收集戶政司驗證碼樣本
- 使用 TensorFlow/PyTorch 訓練專用模型
- 優點：準確率最高
- 缺點：需要大量樣本和時間

---

## 程式碼架構

### 當前實作

```python
class HouseholdCrawler:
    def __init__(self, use_ocr: bool = True):
        # 嘗試初始化 OCR
        if use_ocr and DDDDOCR_AVAILABLE:
            try:
                self.ocr = ddddocr.DdddOcr()
                self.use_ocr = True
            except Exception as e:
                print(f"[OCR] 初始化失敗: {e}")
                self.use_ocr = False
    
    def recognize_captcha(self, image_path: str) -> Optional[str]:
        """自動識別驗證碼"""
        if not self.use_ocr:
            return None
        
        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            
            result = self.ocr.classification(img_bytes)
            
            # 驗證格式（5 個字元）
            if len(result) == 5:
                return result.upper()
            else:
                return None
        except Exception as e:
            print(f"[OCR] 識別失敗: {e}")
            return None
```

### 互動流程

```
1. 初始化爬蟲
   ↓
2. 取得驗證碼圖片
   ↓
3. 嘗試 OCR 識別
   ├─ 成功 → 顯示結果 → 詢問確認
   │         ├─ 確認 → 使用 OCR 結果
   │         └─ 拒絕 → 手動輸入
   └─ 失敗 → 手動輸入
   ↓
4. 執行查詢
```

---

## 測試結果

### ddddocr 測試
```
狀態: ❌ 失敗
原因: Pillow 相容性問題
錯誤: module 'PIL.Image' has no attribute 'ANTIALIAS'
```

### 手動輸入測試
```
狀態: ✅ 成功
準確率: 100%（人工輸入）
速度: ~5 秒/次
```

---

## 下一步建議

### 選項 1：繼續使用手動輸入
**適合情況**：
- 查詢量不大（< 100 次/天）
- 需要 100% 準確率
- 不想處理相容性問題

**操作**：
```python
crawler = HouseholdCrawler(use_ocr=False)
```

### 選項 2：整合 muggle-ocr
**適合情況**：
- 需要自動化
- 可接受 80-90% 準確率
- 願意測試新方案

**步驟**：
1. `pip install muggle-ocr`
2. 修改 `recognize_captcha` 方法
3. 測試識別準確率
4. 調整參數優化

### 選項 3：混合方案（推薦）
**適合情況**：
- 大量查詢需求
- 需要平衡效率和準確率

**策略**：
1. 使用 OCR 自動識別
2. 如果查詢失敗（驗證碼錯誤）
3. 自動重試並要求手動輸入
4. 記錄 OCR 準確率

---

## 常見問題

### Q1: 為什麼不直接降級 Pillow？
**A**: Python 3.13 的 wheel 限制，無法安裝舊版 Pillow。

### Q2: ddddocr 什麼時候會修復？
**A**: 未知。建議關注 GitHub 更新或使用替代方案。

### Q3: 手動輸入會影響效率嗎？
**A**: 
- 單次查詢：影響不大（~5 秒）
- 批量查詢：建議使用 OCR 或等待修復

### Q4: 可以同時使用多個 OCR 嗎？
**A**: 可以。可以實作 fallback 機制：
```python
# 嘗試 ddddocr
result = try_ddddocr(image)
if not result:
    # 嘗試 muggle-ocr
    result = try_muggle_ocr(image)
if not result:
    # 手動輸入
    result = manual_input()
```

---

## 總結

### 目前狀態
- ✅ OCR 框架已整合
- ⚠️ ddddocr 暫時無法使用（Pillow 相容性）
- ✅ 手動輸入備選方案正常運作

### 建議
1. **短期**：繼續使用手動輸入
2. **中期**：測試 muggle-ocr 或其他替代方案
3. **長期**：等待 ddddocr 更新或訓練自定義模型

### 程式碼狀態
- 已保留手動輸入功能（註解保護）
- OCR 功能可隨時啟用（修復後）
- 自動降級機制確保穩定性

---

**最後更新**: 2026/01/07
**狀態**: OCR 框架已整合，等待相容性問題解決
