import openpyxl
from openpyxl.utils.cell import coordinate_to_tuple
from openpyxl.styles import Alignment
from openpyxl.cell.cell import MergedCell


def get_excel_geometry(ws):
    """
    Excelシートの全セル（結合含む）の「仮想的な座標(x, y, w, h)」を計算する。
    単位はポイントや文字数などが混ざるため、相対座標(0.0〜1.0)に正規化して返す。
    """
    # 1. 行の高さと列の幅を累積して、各セルの物理的な開始位置を推定する
    row_heights = {}  # row_idx -> height
    col_widths = {}  # col_idx -> width

    max_row = ws.max_row
    max_col = ws.max_column

    # 行高の取得（設定がない場合はデフォルト値を仮定）
    total_height = 0
    row_starts = {1: 0}
    for r in range(1, max_row + 1):
        h = ws.row_dimensions[r].height
        if h is None:
            h = 13.5  # 標準高さ
        row_heights[r] = h
        total_height += h
        row_starts[r + 1] = total_height

    # 列幅の取得
    total_width = 0
    col_starts = {1: 0}
    for c in range(1, max_col + 1):
        col_letter = openpyxl.utils.get_column_letter(c)
        w = ws.column_dimensions[col_letter].width
        if w is None:
            w = 8.43  # 標準幅
        # 列幅(文字数)を高さ(ポイント)と同じような重みにするための係数（近似）
        # フォントによるが、幅1文字 ≒ 7〜8ポイント程度と仮定
        w_points = w * 7.5
        col_widths[c] = w_points
        total_width += w_points
        col_starts[c + 1] = total_width

    # 2. 全セルのリストアップ
    # 結合セル情報をマップ化
    merge_map = {}
    for rng in ws.merged_cells.ranges:
        min_col, min_row, max_col, max_row = (
            rng.min_col,
            rng.min_row,
            rng.max_col,
            rng.max_row,
        )

        # 結合範囲のピクセルサイズ計算
        x = col_starts[min_col]
        y = row_starts[min_row]
        w = col_starts[max_col + 1] - x
        h = row_starts[max_row + 1] - y

        # 相対座標化
        rect = {
            "r_idx": min_row,
            "c_idx": min_col,
            "rel_x": x / total_width,
            "rel_y": y / total_height,
            "rel_w": w / total_width,
            "rel_h": h / total_height,
            "is_merged": True,
        }

        # 範囲内の全セルがこのrectを参照するようにする
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                merge_map[(r, c)] = rect

    cells_geometry = []

    for r in range(1, max_row + 1):
        for c in range(1, max_col + 1):
            if (r, c) in merge_map:
                # 結合セルの代表（左上）だけをリストに追加
                rect = merge_map[(r, c)]
                if rect["r_idx"] == r and rect["c_idx"] == c:
                    cells_geometry.append(rect)
            else:
                # 通常セル
                x = col_starts[c]
                y = row_starts[r]
                w = col_widths[c]
                h = row_heights[r]
                cells_geometry.append(
                    {
                        "r_idx": r,
                        "c_idx": c,
                        "rel_x": x / total_width,
                        "rel_y": y / total_height,
                        "rel_w": w / total_width,
                        "rel_h": h / total_height,
                        "is_merged": False,
                    }
                )

    return cells_geometry


def fill_text_into_skeleton(skeleton_path, all_pages_elements, output_path):
    """
    人間が編集したスケルトンExcelを読み込み、PDFのテキストを「位置」でマッチングさせて流し込む
    """
    print(f"Loading skeleton: {skeleton_path} ...")
    wb = openpyxl.load_workbook(skeleton_path)

    for page_num, elements in all_pages_elements.items():
        sheet_name = f"Page {page_num}"
        if sheet_name not in wb.sheetnames:
            print(f"[Skip] Sheet '{sheet_name}' not found in Excel.")
            continue

        ws = wb[sheet_name]
        print(f"Processing {sheet_name}...")

        # Excelのセル配置を解析（相対座標 0.0〜1.0 に変換）
        excel_cells = get_excel_geometry(ws)

        # PDFのページサイズ取得
        page_w = 1000  # デフォルト
        page_h = 1000
        for el in elements:
            if el["type"] == "page_size":
                page_w = el["width"]
                page_h = el["height"]
                break

        # PDFテキストの流し込み
        for el in elements:
            if el["type"] != "text":
                continue

            # PDF上の相対座標中心
            cx_pdf = ((el["x0"] + el["x1"]) / 2) / page_w
            cy_pdf = ((el["top"] + el["bottom"]) / 2) / page_h

            # 最も近いExcelセルを探す（中心点距離が最小のもの）
            best_cell = None
            min_dist = float("inf")

            for cell in excel_cells:
                # セルの中心
                cx_cell = cell["rel_x"] + cell["rel_w"] / 2
                cy_cell = cell["rel_y"] + cell["rel_h"] / 2

                # 距離計算（Y方向のズレを重く見る）
                dist = ((cx_pdf - cx_cell) ** 2) + ((cy_pdf - cy_cell) ** 2) * 5

                if dist < min_dist:
                    min_dist = dist
                    best_cell = cell

            # しきい値判定（あまりに遠い場合は書き込まない、とするならここで判定）
            if best_cell:
                r, c = best_cell["r_idx"], best_cell["c_idx"]
                cell_obj = ws.cell(row=r, column=c)

                # 追記ロジック
                # 結合セルの場合、左上に書き込む必要があるが、best_cellには左上が入っている
                current_val = cell_obj.value
                text_to_write = str(el["text"]).strip()

                if current_val:
                    cell_obj.value = str(current_val) + "\n" + text_to_write
                else:
                    cell_obj.value = text_to_write

                # スタイル調整（左上寄せ）
                cell_obj.alignment = Alignment(
                    horizontal="left", vertical="top", wrap_text=True
                )

    wb.save(output_path)
    print(f"\nFinal Excel saved to: {output_path}")
