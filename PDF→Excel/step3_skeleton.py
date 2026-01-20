import bisect
import re
from openpyxl import Workbook
from openpyxl.styles import Border, Side
from openpyxl.utils.cell import get_column_letter


def cluster_coords(coords, tolerance):
    """近接座標の統合"""
    if not coords:
        return []
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


def optimize_grid(cols, rows, elements):
    """罫線が存在しない空のグリッド区間を削除"""
    col_has_content = [False] * (len(cols) - 1)
    row_has_content = [False] * (len(rows) - 1)

    for el in elements:
        if el["type"] not in ["line_h", "line_v"]:
            continue  # 罫線のみ見る

        c_start = bisect.bisect_left(cols, el["x0"] + 2) - 1
        c_end = bisect.bisect_left(cols, el.get("x1", el["x0"]) - 2) - 1
        r_start = bisect.bisect_left(rows, el["top"] + 2) - 1
        r_end = bisect.bisect_left(rows, el.get("bottom", el["top"]) - 2) - 1

        c_start = max(0, c_start)
        r_start = max(0, r_start)
        c_end = min(len(col_has_content) - 1, c_end)
        r_end = min(len(row_has_content) - 1, r_end)

        for c in range(c_start, c_end + 1):
            col_has_content[c] = True
        for r in range(r_start, r_end + 1):
            row_has_content[r] = True

    new_cols = [cols[0]]
    for i, active in enumerate(col_has_content):
        if active or (cols[i + 1] - cols[i] > 100):
            new_cols.append(cols[i + 1])

    new_rows = [rows[0]]
    for i, active in enumerate(row_has_content):
        if active or (rows[i + 1] - rows[i] > 100):
            new_rows.append(rows[i + 1])

    return new_cols, new_rows


def apply_border_safe(ws, r, c, border_type):
    thin = Side(border_style="thin", color="000000")
    try:
        cell = ws.cell(row=r, column=c)
        current = cell.border
        new_sides = {k: getattr(current, k) for k in ["left", "right", "top", "bottom"]}
        if border_type in ["line_h", "all"]:
            new_sides["top"] = thin
            new_sides["bottom"] = thin
        if border_type in ["line_v", "all"]:
            new_sides["left"] = thin
            new_sides["right"] = thin
        cell.border = Border(**new_sides)
    except:
        pass


def generate_skeleton(all_pages_elements, output_path, tolerance=30.0, dpi=300):
    """枠線のみのExcel（スケルトン）を生成"""
    wb = Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    scale_factor = 72 / dpi

    for page_num, elements in all_pages_elements.items():
        ws = wb.create_sheet(title=f"Page {page_num}")
        print(f"Generating Skeleton: Page {page_num}...")

        # 1. グリッド生成（罫線とページサイズのみ使用）
        x_coords = set()
        y_coords = set()

        for el in elements:
            if el["type"] == "page_size":
                x_coords.add(0)
                x_coords.add(el["width"])
                y_coords.add(0)
                y_coords.add(el["height"])
            elif el["type"] in ["line_h", "line_v"]:
                x_coords.add(el["x0"])
                x_coords.add(el["x1"])
                y_coords.add(el["top"])
                y_coords.add(el["bottom"])

        cols = cluster_coords(x_coords, tolerance)
        rows = cluster_coords(y_coords, tolerance)

        # 最適化（テキスト位置を考慮しないため、純粋に罫線構造だけで最適化）
        cols, rows = optimize_grid(cols, rows, elements)

        print(f"  - Skeleton Grid: {len(rows)} rows x {len(cols)} columns")

        # 2. 罫線の描画
        for el in elements:
            if el["type"] not in ["line_h", "line_v"]:
                continue

            c_start = bisect.bisect_left(cols, el["x0"] - tolerance) - 1
            c_end = bisect.bisect_left(cols, el["x1"] - tolerance) - 1
            r_start = bisect.bisect_left(rows, el["top"] - tolerance) - 1
            r_end = bisect.bisect_left(rows, el["bottom"] - tolerance) - 1

            c_start = max(0, c_start)
            c_end = min(len(cols) - 2, c_end)
            r_start = max(0, r_start)
            r_end = min(len(rows) - 2, r_end)

            if c_end < c_start:
                c_end = c_start
            if r_end < r_start:
                r_end = r_start

            for r in range(r_start, r_end + 1):
                for c in range(c_start, c_end + 1):
                    apply_border_safe(ws, r + 1, c + 1, el["type"])

        # 3. サイズ調整
        for i in range(len(cols) - 1):
            w_px = cols[i + 1] - cols[i]
            # Excel幅は適当な係数で換算
            ws.column_dimensions[get_column_letter(i + 1)].width = (
                w_px * scale_factor * 0.13
            )

        for i in range(len(rows) - 1):
            h_px = rows[i + 1] - rows[i]
            ws.row_dimensions[i + 1].height = max(h_px * scale_factor, 13.5)

    try:
        wb.save(output_path)
        print(f"\nSkeleton saved to: {output_path}")
        print(
            "-> Now, please open this Excel file, fix the layout (merge cells, adjust widths), and save/close it."
        )
    except PermissionError:
        print(f"\n[Error] Could not save to {output_path}.")
