import zipfile
import xml.etree.ElementTree as ET
import os
import argparse
import re
import glob
import datetime
import sys

# --- LiteXLSX: Excel Parser (Standard Lib Only) ---

class LiteCell:
    def __init__(self, coordinate, value, data_type, style_idx):
        self.coordinate = coordinate
        self.value = value
        self.data_type = data_type 
        self.style_idx = style_idx
        self.border = False
        self.fill = False
        self.is_date = False
        self.formula = False

class LiteXLSX:
    def __init__(self, filepath):
        self.filepath = filepath
        self.shared_strings = []
        self.styles = {'xfs': []} 
        self.sheets = {} # name -> path
        self.sheet_rels = {} # path -> rels map
        self._load()

    def _get_local_tag(self, element):
        if not hasattr(element, 'tag'): return ""
        if '}' in element.tag:
            return element.tag.split('}', 1)[1]
        return element.tag

    def _load(self):
        try:
            with zipfile.ZipFile(self.filepath, 'r') as z:
                # 1. Shared Strings
                sst_path = None
                for n in z.namelist():
                    if n.lower().endswith('xl/sharedstrings.xml'):
                        sst_path = n; break
                
                if sst_path:
                    with z.open(sst_path) as f:
                        for event, elem in ET.iterparse(f):
                            if self._get_local_tag(elem) == 'si':
                                text_parts = [child.text for child in elem.iter() if self._get_local_tag(child) == 't' and child.text]
                                self.shared_strings.append("".join(text_parts))
                                elem.clear()

                # 2. Styles
                style_path = None
                for n in z.namelist():
                    if n.lower().endswith('xl/styles.xml'):
                        style_path = n; break
                if style_path: self._parse_styles(z.open(style_path))

                # 3. Workbook
                wb_path = None
                for n in z.namelist():
                    if n.lower().endswith('xl/workbook.xml'):
                        wb_path = n; break
                if wb_path: self._parse_workbook(z, wb_path)

        except Exception as e:
            print(f"[ERROR] Init failed: {e}", file=sys.stderr)

    def _parse_styles(self, f):
        try:
            tree = ET.parse(f)
            root = tree.getroot()
            borders, fills = [], []
            
            # Simplified Border/Fill logic
            for node in root.iter():
                tag = self._get_local_tag(node)
                if tag == 'borders':
                    for b in node:
                        borders.append(any(side.get('style') for side in b if self._get_local_tag(side) in ['left','right','top','bottom']))
                elif tag == 'fills':
                    for f in node:
                        has_c = False
                        for p in f:
                            if self._get_local_tag(p) == 'patternFill':
                                for fg in p:
                                    if self._get_local_tag(fg) == 'fgColor':
                                        if fg.get('rgb') and fg.get('rgb') != '00000000': has_c = True
                                        elif fg.get('theme'): has_c = True
                        fills.append(has_c)

            # Date Formats
            date_fmt_ids = set([14,15,16,17,18,19,20,21,22,27,28,29,30,31,32,33,34,35,36,45,46,47])
            for node in root.iter():
                if self._get_local_tag(node) == 'numFmts':
                    for nf in node:
                        if any(c in nf.get('formatCode','').lower() for c in ['d','m','y','h','s']):
                            date_fmt_ids.add(int(nf.get('numFmtId',0)))

            # Xfs
            for node in root.iter():
                if self._get_local_tag(node) == 'cellXfs':
                    for xf in node:
                        bid = int(xf.get('borderId', 0))
                        fid = int(xf.get('fillId', 0))
                        nid = int(xf.get('numFmtId', 0))
                        self.styles['xfs'].append({
                            'border': borders[bid] if bid < len(borders) else False,
                            'fill': fills[fid] if fid < len(fills) and fid >= 2 else False,
                            'is_date': nid in date_fmt_ids
                        })
        except: pass

    def _parse_workbook(self, z, wb_path):
        # Workbook Rels
        rels_path = os.path.dirname(wb_path) + '/_rels/' + os.path.basename(wb_path) + '.rels'
        rels_path = rels_path.replace('\\', '/').lstrip('/')
        
        rid_map = {}
        for n in z.namelist():
            if n.lower() == rels_path.lower():
                try:
                    tree = ET.parse(z.open(n))
                    for rel in tree.getroot():
                        rid_map[rel.get('Id')] = rel.get('Target').replace('xl/xl/', 'xl/').lstrip('/')
                        if not rid_map[rel.get('Id')].startswith('xl/'): rid_map[rel.get('Id')] = 'xl/' + rid_map[rel.get('Id')]
                except: pass; break

        # Sheet Names
        try:
            tree = ET.parse(z.open(wb_path))
            for node in tree.iter():
                if self._get_local_tag(node) == 'sheets':
                    for s in node:
                        name = s.get('name')
                        rid = next((v for k,v in s.attrib.items() if k.endswith('id')), None)
                        if name and rid: self.sheets[name] = rid_map.get(rid, f"xl/worksheets/sheet{s.get('sheetId')}.xml")
        except: pass

    def get_sheet_data(self, sheet_name):
        if sheet_name not in self.sheets: return None, [], False
        
        target_path = self.sheets[sheet_name]
        cells = []
        merged_ranges = []
        has_drawings = False

        try:
            with zipfile.ZipFile(self.filepath, 'r') as z:
                real_path = next((n for n in z.namelist() if os.path.basename(n).lower() == os.path.basename(target_path).lower()), None)
                if not real_path: return None, [], False

                with z.open(real_path) as f:
                    for event, elem in ET.iterparse(f):
                        tag = self._get_local_tag(elem)
                        
                        if tag == 'mergeCell':
                            if elem.get('ref'): merged_ranges.append(elem.get('ref'))
                        
                        elif tag == 'drawing': # 画像/図形の存在チェック
                            has_drawings = True

                        elif tag == 'c':
                            coord = elem.get('r')
                            t = elem.get('t', 'n')
                            s_idx = int(elem.get('s', 0))
                            
                            raw = None
                            inline = ""
                            has_f = False
                            for child in elem:
                                ctag = self._get_local_tag(child)
                                if ctag == 'v': raw = child.text
                                elif ctag == 'f': has_f = True
                                elif ctag == 'is': 
                                    inline = "".join([t.text for t in child.iter() if self._get_local_tag(t)=='t' and t.text])

                            val = raw
                            if t == 's' and raw:
                                val = self.shared_strings[int(raw)] if int(raw) < len(self.shared_strings) else ""
                            elif t == 'inlineStr': val = inline
                            elif t == 'b': val = (raw == '1')
                            
                            cobj = LiteCell(coord, val, t, s_idx)
                            cobj.formula = has_f
                            
                            if s_idx < len(self.styles['xfs']):
                                st = self.styles['xfs'][s_idx]
                                cobj.border = st['border']
                                cobj.fill = st['fill']
                                if st['is_date'] and raw:
                                    try: 
                                        cobj.value = (datetime.datetime(1899,12,30)+datetime.timedelta(days=float(raw))).strftime("%Y-%m-%d")
                                    except: pass
                            
                            cells.append(cobj)
                            elem.clear()

        except Exception as e:
            print(f"[ERROR] Sheet parse error: {e}", file=sys.stderr)
            return None, [], False

        return cells, merged_ranges, has_drawings

# --- Mapper Logic ---

class ExcelMapper:
    def __init__(self, file_path):
        self.xlsx = LiteXLSX(file_path)

    def _coord_to_rc(self, coord):
        m = re.match(r"([A-Z]+)([0-9]+)", coord)
        if not m: return 0,0
        col_str, row_str = m.groups()
        col = 0
        for c in col_str: col = col * 26 + (ord(c) - 64)
        return int(row_str), col

    def _rc_to_coord(self, r, c):
        res = ""
        while c > 0:
            c, rem = divmod(c - 1, 26)
            res = chr(65 + rem) + res
        return f"{res}{r}"

    def _expand_merge(self, ref):
        # "A1:B2" -> (1,1,2,2) (min_r, min_c, max_r, max_c)
        start, end = ref.split(':')
        r1, c1 = self._coord_to_rc(start)
        r2, c2 = self._coord_to_rc(end)
        return (min(r1,r2), min(c1,c2), max(r1,r2), max(c1,c2))

    def analyze_sheet(self, sheet_name):
        cells, merged_ranges, has_drawings = self.xlsx.get_sheet_data(sheet_name)
        if cells is None: return "Error loading sheet."

        # Map Cells
        cell_map = {}
        max_r, max_c = 0, 0
        for c in cells:
            r, col = self._coord_to_rc(c.coordinate)
            cell_map[(r,col)] = c
            max_r = max(max_r, r)
            max_c = max(max_c, col)
        
        # Merge Map: (r,c) -> "TopLeftCoord"
        merge_map = {}
        for rng in merged_ranges:
            if ':' in rng:
                rmin, cmin, rmax, cmax = self._expand_merge(rng)
                top_left = self._rc_to_coord(rmin, cmin)
                for r in range(rmin, rmax+1):
                    for c in range(cmin, cmax+1):
                        if r==rmin and c==cmin: continue # Skip top-left itself
                        merge_map[(r,c)] = top_left

        max_r = min(max_r, 300)
        max_c = min(max_c, 50)

        lines = [f"=== SHEET: {sheet_name} ==="]
        if has_drawings: lines.append("[INFO] This sheet contains Images/Charts/Shapes (detected but not rendered).")
        lines.append(f"Merged Ranges: {', '.join(merged_ranges)}")
        lines.append("-" * 60)

        raw_rows = []
        for r in range(1, max_r + 1):
            row_items = []
            has_data = False
            for c in range(1, max_c + 1):
                # 結合されたセル（隠れているセル）の処理
                if (r,c) in merge_map:
                    # 結合されていることを明示 (例: <MERGED_WITH_A1>)
                    # ノイズが多いようならこの行はコメントアウトしてスキップにしても良い
                    # row_items.append(f"[{self._rc_to_coord(r,c)}] <MERGED_WITH_{merge_map[(r,c)]}>")
                    continue 

                cell = cell_map.get((r,c))
                if not cell: continue

                val = str(cell.value).strip() if cell.value is not None else ""
                tags = []
                if cell.fill: tags.append("BG:COLOR")
                if cell.border: tags.append("BORDER")
                
                txt = ""
                if val:
                    if cell.is_date: tags.append("DATE")
                    if cell.formula: tags.append("FORMULA")
                    txt = f"{val} <{' '.join(tags)}>" if tags else val
                else:
                    if tags: txt = f"{{_INPUT_}} <{' '.join(tags)}>"
                
                if txt:
                    row_items.append(f"[{cell.coordinate}] {txt}")
                    has_data = True
            
            raw_rows.append(" | ".join(row_items) if has_data else "<EMPTY_ROW>")

        # Compress
        compressed = []
        if raw_rows:
            curr = raw_rows[0]
            curr_sig = re.sub(r'\[[A-Z0-9]+\] ', '', curr)
            count = 0
            for line in raw_rows[1:]:
                sig = re.sub(r'\[[A-Z0-9]+\] ', '', line)
                if line == curr or (line != "<EMPTY_ROW>" and sig == curr_sig):
                    count += 1
                else:
                    compressed.append(curr)
                    if count > 0: compressed.append(f"... (Repeated {count} rows) ...")
                    curr = line; curr_sig = sig; count = 0
            compressed.append(curr)
            if count > 0: compressed.append(f"... (Repeated {count} rows) ...")

        return "\n".join(lines + compressed)

if __name__ == "__main__":
    import glob
    files = glob.glob("*.xlsx")
    if files:
        print(f"Scanning {len(files)} files...")
        for f in files:
            print(f"\nFILE: {f}")
            print(ExcelMapper(f).analyze_sheet(next(iter(LiteXLSX(f).sheets), None)))
    else:
        print("No .xlsx files found.")