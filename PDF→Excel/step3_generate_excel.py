import bisect
import re
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side
from openpyxl.utils.cell import get_column_letter
from openpyxl.cell.cell import MergedCell # 追加

def clean_text(text):
    """Excelで保存できない不正な制御文字を除去し、数式誤認を防ぐ"""
    if text is None: return ""
    text = str(text)
    # 制御文字除去
    text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # 数式エスケープ
    if text.startswith("="):
        text = "'" + text
    return text

def cluster_coords(coords, tolerance):
    """近接座標の統合"""
    if not coords: return []
    sorted_coords = sorted(list(coords))
    clusters = []
    current_cluster = [sorted_coords[0]]
    for c in sorted_coords[1:]:
        if c - current_cluster[-1] <= tolerance:
            current_cluster.append(c)
        else:
            clusters.append(min(current_cluster))
            current_cluster = [c]
    clusters.append(min(current_cluster))
    return clusters

def optimize_grid(cols, rows, elements, tolerance):
    """空のグリッド区間を削除"""
    col_has_content = [False] * (len(cols) - 1)
    row_has_content = [False] * (len(rows) - 1)
    
    for el in elements:
        if el['type'] == 'page_size': continue
        
        c_start = bisect.bisect_left(cols, el['x0'] + 2) - 1
        c_end = bisect.bisect_left(cols, el.get('x1', el['x0']) - 2) - 1
        r_start = bisect.bisect_left(rows, el['top'] + 2) - 1
        r_end = bisect.bisect_left(rows, el.get('bottom', el['top']) - 2) - 1
        
        c_start = max(0, c_start)
        r_start = max(0, r_start)
        c_end = min(len(col_has_content)-1, c_end)
        r_end = min(len(row_has_content)-1, r_end)

        for c in range(c_start, c_end + 1): col_has_content[c] = True
        for r in range(r_start, r_end + 1): row_has_content[r] = True

    new_cols = [cols[0]]
    for i, active in enumerate(col_has_content):
        if active or (cols[i+1] - cols[i] > 150):
            new_cols.append(cols[i+1])
            
    new_rows = [rows[0]]
    for i, active in enumerate(row_has_content):
        if active or (rows[i+1] - rows[i] > 150):
            new_rows.append(rows[i+1])
            
    return new_cols, new_rows

def apply_border_safe(ws, r, c, border_type):
    """枠線適用（安全版）"""
    thin = Side(border_style="thin", color="000000")
    try:
        cell = ws.cell(row=r, column=c)
        # 結合セルの場合、スタイル適用は無視するか、親を探す必要があるが
        # 枠線に関してはエラーが出にくいのでそのままトライ
        current = cell.border
        new_sides = {k: getattr(current, k) for k in ['left', 'right', 'top', 'bottom']}
        if border_type in ['line_h', 'all']:
            new_sides['top'] = thin
            new_sides['bottom'] = thin
        if border_type in ['line_v', 'all']:
            new_sides['left'] = thin
            new_sides['right'] = thin
        cell.border = Border(**new_sides)
    except: pass

def get_master_cell(ws, cell):
    """結合セルの場合、その親（左上）のセルを返す"""
    if isinstance(cell, MergedCell):
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                return ws.cell(row=merged_range.min_row, column=merged_range.min_col)
    return cell

def generate_excel(all_pages_elements, output_path, tolerance=30.0, dpi=300):
    wb = Workbook()
    if "Sheet" in wb.sheetnames: del wb["Sheet"]
    scale_factor = 72 / dpi 

    for page_num, elements in all_pages_elements.items():
        ws = wb.create_sheet(title=f"Page {page_num}")
        print(f"Generating Sheet: Page {page_num}...")

        # --- 1. グリッド生成 ---
        x_coords = set()
        y_coords = set()
        page_w = 0
        
        for el in elements:
            if el['type'] == 'page_size':
                page_w = el['width']
                x_coords.add(0); x_coords.add(page_w)
                y_coords.add(0); y_coords.add(el['height'])
            elif el['type'] in ['line_h', 'line_v']:
                x_coords.add(el['x0']); x_coords.add(el['x1'])
                y_coords.add(el['top']); y_coords.add(el['bottom'])
            elif el['type'] == 'text':
                x_coords.add(el['x0'])
                y_coords.add(el['top'])

        if page_w == 0:
             x_coords.add(0); x_coords.add(2000)
             y_coords.add(0); y_coords.add(2000)

        cols = cluster_coords(x_coords, tolerance)
        rows = cluster_coords(y_coords, tolerance)
        
        cols, rows = optimize_grid(cols, rows, elements, tolerance)
        print(f"  - Final Grid: {len(rows)} rows x {len(cols)} columns")

        # --- 2. 配置 ---
        occupied_cells = set()
        col_max_chars = {}

        # テキスト優先でソート
        sorted_elements = sorted(elements, key=lambda x: 0 if x['type'] == 'text' else 1)

        for el in sorted_elements:
            if el['type'] == 'page_size': continue

            if el['type'] == 'text':
                cx, cy = el['x0'] + 2, (el['top'] + el['bottom']) / 2
            else:
                cx, cy = (el['x0'] + el['x1']) / 2, (el['top'] + el['bottom']) / 2

            c_idx = bisect.bisect_left(cols, cx) - 1
            r_idx = bisect.bisect_left(rows, cy) - 1
            
            c_idx = max(0, min(c_idx, len(cols) - 2))
            r_idx = max(0, min(r_idx, len(rows) - 2))
            
            excel_c, excel_r = c_idx + 1, r_idx + 1

            # --- テキスト処理 ---
            if el['type'] == 'text':
                safe_text = clean_text(el['text'])
                text_len = sum([2 if ord(c) > 256 else 1 for c in safe_text])
                col_max_chars[excel_c] = max(col_max_chars.get(excel_c, 0), text_len)

                # 結合判定
                text_right = el['x1']
                cell_right = cols[c_idx + 1]
                c_span = 0
                
                if text_right > cell_right + tolerance:
                    span_end_idx = bisect.bisect_left(cols, text_right - tolerance) - 1
                    possible_span = max(0, span_end_idx - c_idx)
                    
                    is_safe_merge = True
                    for k in range(1, possible_span + 1):
                        if (excel_r, excel_c + k) in occupied_cells:
                            is_safe_merge = False
                            break
                    if is_safe_merge:
                        c_span = possible_span

                cell_key = (excel_r, excel_c)
                
                try:
                    cell = ws.cell(row=excel_r, column=excel_c)
                    
                    # ★修正ポイント: MergedCell対策
                    # 既に結合されているセルに当たった場合、その親を探して追記する
                    if isinstance(cell, MergedCell):
                        master = get_master_cell(ws, cell)
                        if master.value:
                            master.value = str(master.value) + " " + safe_text
                        else:
                            master.value = safe_text
                    else:
                        # 通常セルの場合
                        cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

                        if cell_key in occupied_cells:
                            # 自分が開始点だが既にデータがある場合（追記）
                            if cell.value: cell.value = str(cell.value) + " " + safe_text
                            else: cell.value = safe_text
                        else:
                            # 新規書き込み
                            cell.value = safe_text
                            occupied_cells.add(cell_key)
                            
                            # 結合実行
                            if c_span > 0:
                                ws.merge_cells(start_row=excel_r, start_column=excel_c,
                                               end_row=excel_r, end_column=excel_c + c_span)
                                for k in range(1, c_span + 1):
                                    occupied_cells.add((excel_r, excel_c + k))
                                    
                except Exception as e:
                    print(f"    [Warning] Cell write error at {excel_r},{excel_c}: {e}")

            # --- 罫線処理 ---
            elif el['type'] in ['line_h', 'line_v']:
                c_start_idx = bisect.bisect_left(cols, el['x0'] - tolerance) - 1
                c_end_idx = bisect.bisect_left(cols, el['x1'] - tolerance) - 1
                r_start_idx = bisect.bisect_left(rows, el['top'] - tolerance) - 1
                r_end_idx = bisect.bisect_left(rows, el['bottom'] - tolerance) - 1
                
                c_start_idx = max(0, c_start_idx)
                c_end_idx = min(len(cols)-2, c_end_idx)
                r_start_idx = max(0, r_start_idx)
                r_end_idx = min(len(rows)-2, r_end_idx)
                
                if c_end_idx < c_start_idx: c_end_idx = c_start_idx
                if r_end_idx < r_start_idx: r_end_idx = r_start_idx

                for r in range(r_start_idx, r_end_idx + 1):
                    for c in range(c_start_idx, c_end_idx + 1):
                        apply_border_safe(ws, r+1, c+1, el['type'])

        # --- サイズ調整 ---
        for i in range(len(cols) - 1):
            w_px = cols[i+1] - cols[i]
            w_base = w_px * scale_factor * 0.14
            w_text = col_max_chars.get(i+1, 0) * 1.3
            final_w = max(w_base, w_text)
            ws.column_dimensions[get_column_letter(i+1)].width = min(final_w, 60)

        for i in range(len(rows) - 1):
            h_px = rows[i+1] - rows[i]
            ws.row_dimensions[i+1].height = max(h_px * scale_factor, 13.5)

    try:
        wb.save(output_path)
        print(f"\nSaved Excel to: {output_path}")
    except PermissionError:
        print(f"\n[Error] Could not save to {output_path}. Please close the file in Excel and try again.")