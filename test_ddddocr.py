"""
測試 ddddocr 對戶政司驗證碼的識別效果
"""
import os
from pathlib import Path

# ============================================================
# 修正 Pillow 12.x 相容性問題
# Pillow 10.0.0 移除了 ANTIALIAS，改用 LANCZOS
# ============================================================
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
    print("[修正] 已將 Image.ANTIALIAS 指向 Image.LANCZOS")
# ============================================================

import ddddocr

# 初始化 OCR
print("初始化 ddddocr...")
ocr = ddddocr.DdddOcr()
print("✓ 初始化成功")

print("=" * 60)
print("測試 ddddocr 驗證碼識別")
print("=" * 60)

img_dir = Path("test_images")  # 你的資料夾名稱
# 測試現有的驗證碼圖片
test_images = [
    "test_captcha_6.png",
    "test_captcha_7.png",
    "test_captcha_8.png",
    "test_captcha_9.png",
    "test_captcha_10.png",
    "test_captcha_11.png",
    "test_captcha_12.png",
    "test_captcha_13.png",
    "test_captcha_14.png",
    "test_captcha_15.png",
    "test_captcha_16.png",
    "test_captcha_17.png",
    "test_captcha_18.png",
    "test_captcha_19.png",
    "test_captcha_20.png",
]

results = []

for img_name in test_images:
    img_path = img_dir / img_name
    if not img_path.exists():
        continue
    
    try:
        with open(img_path, "rb") as f:
            img_bytes = f.read()
        
        result = ocr.classification(img_bytes)
        results.append((img_name, result, len(result)))
        
        print(f"\n{img_name}:")
        print(f"  識別結果: {result}")
        print(f"  長度: {len(result)} 字元")
        
    except Exception as e:
        print(f"\n{img_name}:")
        print(f"  錯誤: {e}")

# 統計
print("\n" + "=" * 60)
print("統計結果")
print("=" * 60)

if results:
    lengths = [r[2] for r in results]
    print(f"測試圖片數: {len(results)}")
    print(f"識別長度範圍: {min(lengths)} - {max(lengths)} 字元")
    print(f"\n所有識別結果:")
    for name, result, length in results:
        print(f"  {name:30s} → {result:10s} ({length} 字元)")
else:
    print("沒有找到測試圖片")

print("\n提示: 戶政司驗證碼格式為 5 個字元（數字+大寫字母）")
