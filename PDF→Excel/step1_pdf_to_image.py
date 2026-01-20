import numpy as np
from pdf2image import convert_from_path
import os
from PIL import Image

def convert_all_pages_to_numpy(pdf_path, dpi=300):
    """
    PDFの全ページを高解像度で画像化し、OpenCVで扱えるNumPy配列のリストとして返す
    
    Args:
        pdf_path (str): PDFファイルのパス
        dpi (int): 解像度 (OCR精度向上のため300推奨)
    
    Returns:
        list: [(page_number, numpy_array), ...] のリスト
    """
    
    # ファイルの存在確認
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    print(f"Processing: {pdf_path}")

    try:
        # pdf2imageを使ってPDFの全ページを一括変換
        # ページ数が多い場合は時間がかかることがあります
        pil_images = convert_from_path(pdf_path, dpi=dpi)
        
        if not pil_images:
            raise ValueError("Failed to convert PDF to images.")

        results = []
        
        for i, pil_image in enumerate(pil_images):
            page_num = i + 1
            
            # PIL画像をNumPy配列に変換 (OpenCV等の処理用)
            image_np = np.array(pil_image)
            
            results.append((page_num, image_np))
            print(f"  - Converted Page {page_num} (Size: {image_np.shape})")
            
        return results

    except Exception as e:
        print(f"Error converting PDF: {e}")
        return []

# --- 動作確認用メイン処理 ---
if __name__ == "__main__":
    # 対象のPDFファイル名
    target_pdf = "ts.pdf" 
    
    # 実行
    page_data_list = convert_all_pages_to_numpy(target_pdf)
    
    if page_data_list:
        print(f"\nTotal {len(page_data_list)} pages converted successfully.")
        
        # 確認用に画像を保存
        output_dir = "debug_images"
        os.makedirs(output_dir, exist_ok=True)
        
        for page_num, img_array in page_data_list:
            output_filename = os.path.join(output_dir, f"page_{page_num:02d}.png")
            
            # NumPy配列をPIL画像に戻して保存
            Image.fromarray(img_array).save(output_filename)
            print(f"Saved debug image: {output_filename}")
            
        print("\nStep 1 Complete. Ready for Step 2 (Line Detection).")
    else:
        print("Conversion failed.")