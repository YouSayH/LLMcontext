import sys
import os

# 各ステップのモジュールをインポート
try:
    from step1_pdf_to_image import convert_all_pages_to_numpy
    from step2_analyze_layout import analyze_page
    from step3_generate_excel import generate_excel
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure step1_..., step2_..., step3_... .py files are in the same directory.")
    sys.exit(1)

def main():
    # 入力ファイル設定
    input_pdf = "ts.pdf"       # ターゲットのPDFファイル名
    output_xlsx = "ts_converted.xlsx"  # 出力するExcelファイル名
    
    # ファイル存在確認
    if not os.path.exists(input_pdf):
        print(f"Error: {input_pdf} not found.")
        return

    # --- Step 1: 画像化 ---
    print("\n=== Step 1: Converting PDF to Images ===")
    page_data_list = convert_all_pages_to_numpy(input_pdf, dpi=300)
    
    if not page_data_list:
        print("Failed to convert PDF. Exiting.")
        return

    # --- Step 2: 解析 (罫線検出 & OCR) ---
    print("\n=== Step 2: Analyzing Layout ===")
    all_pages_elements = {}
    
    for page_num, img_array in page_data_list:
        print(f"Processing Page {page_num}...")
        elements = analyze_page(img_array)
        all_pages_elements[page_num] = elements
        
    # --- Step 3: Excel生成 ---
    print("\n=== Step 3: Generating Excel ===")
    # グリッドの吸着強度（許容誤差）
    # 画像サイズが大きい(3500px)ので、15px〜20pxくらいのズレは許容しないと行が増えすぎます
    generate_excel(all_pages_elements, output_xlsx, tolerance=15.0)

    print("\nAll done! Please check the output file.")

if __name__ == "__main__":
    main()