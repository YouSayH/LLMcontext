import cv2
import numpy as np
from onnxocr.onnx_paddleocr import ONNXPaddleOcr

# Step 1のモジュールをインポート
try:
    from step1_pdf_to_image import convert_all_pages_to_numpy
except ImportError:
    pass


def detect_lines(image_np):
    """
    OpenCVを使って画像から「水平線」と「垂直線」を検出する
    """
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np

    # 二値化
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    elements = []
    h_img, w_img = image_np.shape[:2]

    # --- ユーザー指定の閾値（かなり大きめ） ---
    # 画像の端にある枠線などを確実に拾うため、あるいは大枠だけ拾うための設定
    min_w_len = w_img // 10
    min_h_len = h_img // 20

    # --- A. 横線の検出 ---
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_w_len, 1))
    h_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    cnts, _ = cv2.findContours(h_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w >= min_w_len:
            elements.append(
                {
                    "type": "line_h",
                    "x0": x,
                    "top": y,
                    "x1": x + w,
                    "bottom": y + h,
                    "width": w,
                    "height": h,
                }
            )

    # --- B. 縦線の検出 ---
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_h_len))
    v_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)
    cnts, _ = cv2.findContours(v_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if h >= min_h_len:
            elements.append(
                {
                    "type": "line_v",
                    "x0": x,
                    "top": y,
                    "x1": x + w,
                    "bottom": y + h,
                    "width": w,
                    "height": h,
                }
            )

    print(
        f"  - Lines detected: {len(elements)} (threshold w>{min_w_len}, h>{min_h_len})"
    )
    return elements


def run_ocr(image_np):
    """OnnxOCRを実行"""
    print("  - Running OnnxOCR...")
    ocr = ONNXPaddleOcr(use_gpu=False, lang="japan")
    result = ocr.ocr(image_np)

    elements = []
    if not result:
        return elements

    for line in result:
        if not line:
            continue
        items = (
            [line]
            if (isinstance(line, list) and len(line) == 2 and isinstance(line[0], list))
            else line
        )

        for item in items:
            if not isinstance(item, list) or len(item) != 2:
                continue

            box, (text, score) = item
            if score < 0.5:
                continue

            xs = [p[0] for p in box]
            ys = [p[1] for p in box]

            x0, x1 = int(min(xs)), int(max(xs))
            top, bottom = int(min(ys)), int(max(ys))

            elements.append(
                {
                    "type": "text",
                    "text": text,
                    "x0": x0,
                    "top": top,
                    "x1": x1,
                    "bottom": bottom,
                    "score": score,
                }
            )

    print(f"  - Text blocks detected: {len(elements)}")
    return elements


def analyze_page(image_np):
    """
    解析メイン処理
    """
    # 1. 検出
    raw_lines = detect_lines(image_np)
    texts = run_ocr(image_np)

    # 画像サイズ情報を「特別な要素」として追加
    # これをStep 3で受け取って、外枠グリッドを作るのに使います
    h, w = image_np.shape[:2]
    page_info = [
        {
            "type": "page_size",
            "width": w,
            "height": h,
            "x0": 0,
            "top": 0,
            "x1": w,
            "bottom": h,  # ダミー座標
        }
    ]

    # 2. 統合
    return raw_lines + texts + page_info


if __name__ == "__main__":
    target_pdf = "ts.pdf"
    print("--- Step 1: Converting ---")
    page_data_list = convert_all_pages_to_numpy(target_pdf)
    if page_data_list:
        print("\n--- Step 2: Analyzing ---")
        analyze_page(page_data_list[0][1])
