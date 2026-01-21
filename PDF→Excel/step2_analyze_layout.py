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
    ★修正点: 検出後に太い線を「中心線」に補正して、二重線（四角認識）を防ぎます。
    """
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np

    # 二値化
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    elements = []
    h_img, w_img = image_np.shape[:2]

    # --- ユーザー指定の閾値 ---
    min_w_len = w_img // 10
    min_h_len = h_img // 20

    # --- A. 横線の検出 ---
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_w_len, 1))
    h_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)

    # 途切れ対策: 縦に膨張させて結合
    kernel_h_join = np.ones((5, 1), np.uint8)
    h_lines_img = cv2.dilate(h_lines_img, kernel_h_join, iterations=1)

    cnts, _ = cv2.findContours(h_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w >= min_w_len:
            # ▼▼▼ 修正: 中心線（芯）をとる ▼▼▼
            # 太い線として検出されても、中心のY座標を使って「細い線」として登録する
            center_y = y + h // 2
            # 上下1pxずつの幅2pxの線として定義しなおす
            new_top = center_y - 1
            new_bottom = center_y + 1
            
            elements.append(
                {
                    "type": "line_h",
                    "x0": x,
                    "top": new_top,      # 修正済み座標
                    "x1": x + w,
                    "bottom": new_bottom, # 修正済み座標
                    "width": w,
                    "height": 2,          # 高さを強制的に2pxにする
                }
            )

    # --- B. 縦線の検出 ---
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_h_len))
    v_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 途切れ対策: 横に膨張させて結合
    kernel_v_join = np.ones((1, 5), np.uint8)
    v_lines_img = cv2.dilate(v_lines_img, kernel_v_join, iterations=1)

    cnts, _ = cv2.findContours(v_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if h >= min_h_len:
            # ▼▼▼ 修正: 中心線（芯）をとる ▼▼▼
            # 太い線として検出されても、中心のX座標を使って「細い線」として登録する
            center_x = x + w // 2
            # 左右1pxずつの幅2pxの線として定義しなおす
            new_x0 = center_x - 1
            new_x1 = center_x + 1

            elements.append(
                {
                    "type": "line_v",
                    "x0": new_x0,        # 修正済み座標
                    "top": y,
                    "x1": new_x1,        # 修正済み座標
                    "bottom": y + h,
                    "width": 2,          # 幅を強制的に2pxにする
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
    OpenCVは BGR 形式なので、赤色は (0, 0, 255) です。
    """
    # 元画像を汚さないようにコピーを作成
    debug_img = image_np.copy()

    for el in elements:
        if el['type'] == 'page_size':
            continue

        x0, y0 = int(el['x0']), int(el['top'])
        x1, y1 = int(el['x1']), int(el['bottom'])

        if el['type'] == 'text':
            # ★ テキストを赤枠 (Blue=0, Green=0, Red=255) に設定
            cv2.rectangle(debug_img, (x0, y0), (x1, y1), (0, 0, 255), 2)
            
        elif el['type'] in ['line_h', 'line_v']:
            # 罫線は区別しやすいように緑色 (Blue=0, Green=255, Red=0) に設定
            # 補正後の細い線が描画されるため、太い黒線の「真ん中」に細い緑線が引かれます
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