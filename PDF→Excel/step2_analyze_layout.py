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
    ・中心線補正: 太い線を1本の線にする
    ・ノイズ除去: 短すぎる線を無視する
    """
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np

    # 二値化
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    elements = []
    h_img, w_img = image_np.shape[:2]

    # --- 1. 閾値の設定（調整済み） ---
    # 元は // 10 でしたが、細かい表の線を拾えるように少し緩くします
    min_w_len = w_img // 20  
    min_h_len = h_img // 30

    # --- A. 横線の検出 ---
    # 横長の構造要素で抽出
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_w_len, 1))
    h_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)

    # 途切れ対策: 縦に少し膨張させて結合
    kernel_h_join = np.ones((4, 1), np.uint8)
    h_lines_img = cv2.dilate(h_lines_img, kernel_h_join, iterations=1)

    cnts, _ = cv2.findContours(h_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        
        # 【追加】ノイズ除去: 極端に短い線（例えば50px未満）は無視
        if w < 50:
            continue

        # 中心線（芯）をとる
        center_y = y + h // 2
        elements.append(
            {
                "type": "line_h",
                "x0": x,
                "top": center_y - 1,
                "x1": x + w,
                "bottom": center_y + 1,
                "width": w,
                "height": 2, # 強制的に細くする
            }
        )

    # --- B. 縦線の検出 ---
    # 縦長の構造要素で抽出
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_h_len))
    v_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 途切れ対策: 横に少し膨張させて結合
    kernel_v_join = np.ones((1, 4), np.uint8)
    v_lines_img = cv2.dilate(v_lines_img, kernel_v_join, iterations=1)

    cnts, _ = cv2.findContours(v_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)

        # 【追加】ノイズ除去: 極端に短い線は無視
        if h < 20:
            continue

        # 中心線（芯）をとる
        center_x = x + w // 2
        elements.append(
            {
                "type": "line_v",
                "x0": center_x - 1,
                "top": y,
                "x1": center_x + 1,
                "bottom": y + h,
                "width": 2, # 強制的に細くする
                "height": h,
            }
        )

    print(f"  - Lines detected: {len(elements)}")
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
    h, w = image_np.shape[:2]
    page_info = [
        {
            "type": "page_size",
            "width": w,
            "height": h,
            "x0": 0,
            "top": 0,
            "x1": w,
            "bottom": h,
        }
    ]

    # 2. 統合
    return raw_lines + texts + page_info


def save_debug_image(image_np, elements, output_path):
    """
    解析結果（テキスト・罫線）を画像に描画して保存する
    """
    # 元画像を汚さないようにコピーを作成
    debug_img = image_np.copy()

    for el in elements:
        if el['type'] == 'page_size':
            continue

        x0, y0 = int(el['x0']), int(el['top'])
        x1, y1 = int(el['x1']), int(el['bottom'])

        if el['type'] == 'text':
            # テキストを赤枠
            cv2.rectangle(debug_img, (x0, y0), (x1, y1), (0, 0, 255), 2)
            
        elif el['type'] in ['line_h', 'line_v']:
            # 罫線は緑枠
            cv2.rectangle(debug_img, (x0, y0), (x1, y1), (0, 255, 0), 2)

    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, debug_img)
    print(f"  [Debug] Saved visualization to: {output_path}")


if __name__ == "__main__":
    target_pdf = "ts.pdf"
    print("--- Step 1: Converting ---")
    
    page_data_list = convert_all_pages_to_numpy(target_pdf)
    
    if page_data_list:
        print("\n--- Step 2: Analyzing & Visualizing ---")
        
        for page_num, img_array in page_data_list:
            print(f"Processing Page {page_num}...")
            elements = analyze_page(img_array)
            output_filename = f"debug_analyzed/page_{page_num:02d}_result.png"
            save_debug_image(img_array, elements, output_filename)