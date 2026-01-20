import os
import sys

# 各モジュールのインポート
try:
    from step1_pdf_to_image import convert_all_pages_to_numpy
    from step2_analyze_layout import analyze_page
    from step3_skeleton import generate_skeleton
    from step4_fill_text import fill_text_into_skeleton
except ImportError:
    print(
        "Error: Make sure step1, step2, step3_skeleton, step4_fill_text are in the same folder."
    )
    sys.exit(1)


def main():
    input_pdf = "ts.pdf"
    skeleton_xlsx = "skeleton.xlsx"  # 一時ファイル（編集用）
    final_xlsx = "final_output.xlsx"  # 完成ファイル

    print("=== Phase 1: Create Skeleton (Borders Only) ===")

    # 1. PDF読み込みと解析（ここは常に必要）
    # ※解析結果をキャッシュ（保存）しておくと、Phase 2で再解析しなくて済むので高速ですが
    #   今回はシンプルにするため毎回走らせます。

    print("Reading PDF...")
    page_data_list = convert_all_pages_to_numpy(input_pdf, dpi=300)
    all_pages_elements = {}
    for page_num, img in page_data_list:
        print(f"Analyzing Page {page_num}...")
        all_pages_elements[page_num] = analyze_page(img)

    # 2. スケルトン生成
    if not os.path.exists(skeleton_xlsx):
        generate_skeleton(all_pages_elements, skeleton_xlsx, tolerance=40.0)
        print("\n" + "=" * 60)
        print(f"【重要】 {skeleton_xlsx} が作成されました。")
        print("1. Excelでこのファイルを開いてください。")
        print(
            "2. セルの結合、行・列の削除、幅の調整などを行って、『見た目』を整えてください。"
        )
        print("   ※テキストはまだ入っていません。枠線だけ整えてください。")
        print("3. 保存して、Excelを閉じてください。")
        print("4. 準備ができたら、Enterキーを押してください...")
        print("=" * 60)
        input("Press Enter to continue to Phase 2...")
    else:
        print(f"\nFound existing {skeleton_xlsx}. Using it as the template.")
        print("If you want to regenerate it, delete the file and restart.")

    print("\n=== Phase 2: Fill Text into Your Template ===")

    # 3. テキスト流し込み
    try:
        fill_text_into_skeleton(skeleton_xlsx, all_pages_elements, final_xlsx)
        print("\nSUCCESS! Check 'final_output.xlsx'")
    except Exception as e:
        print(f"Error during text filling: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
