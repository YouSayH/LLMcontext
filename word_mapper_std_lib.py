import zipfile
import xml.etree.ElementTree as ET
import os
import argparse
import sys
import shutil
from collections import Counter

# OOXML Namespaces
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "v": "urn:schemas-microsoft-com:vml",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}


class WordMapper:
    def __init__(self, docx_path, image_output_dir="extracted_images"):
        self.docx_path = docx_path
        self.image_output_dir = image_output_dir
        self.rels_map = {}
        self.doc_xml = None
        self.styles_xml = None
        self.media_files = {}
        self.styles_map = {}

        self.smartart_data = {}
        self.chart_data = {}

        self.default_styles = {"color": None, "size": None, "bg": None, "style": None}

    def analyze(self):
        if not os.path.exists(self.docx_path):
            return f"Error: File '{self.docx_path}' not found."

        try:
            with zipfile.ZipFile(self.docx_path, "r") as z:
                self._parse_rels(z)
                self._extract_images(z)

                if "word/styles.xml" in z.namelist():
                    self.styles_xml = z.read("word/styles.xml")
                    self._parse_styles_xml()

                self._preload_external_data(z)

                try:
                    self.doc_xml = z.read("word/document.xml")
                except KeyError:
                    return "Error: Invalid docx file (word/document.xml not found)."

            self._detect_default_styles()
            return self._generate_map()

        except zipfile.BadZipFile:
            return "Error: Invalid docx file (not a zip archive)."
        except Exception as e:
            import traceback

            return f"Error during analysis: {str(e)}\n{traceback.format_exc()}"

    def _parse_rels(self, z):
        try:
            xml_content = z.read("word/_rels/document.xml.rels")
            root = ET.fromstring(xml_content)
            for rel in root:
                rid = rel.get("Id")
                target = rel.get("Target")
                if target:
                    if (
                        target.startswith("media/")
                        or target.startswith("diagrams/")
                        or target.startswith("charts/")
                    ):
                        target = "word/" + target
                    elif not target.startswith("word/") and not target.startswith(
                        "http"
                    ):
                        target = "word/" + target
                    self.rels_map[rid] = target
        except KeyError:
            pass

    def _preload_external_data(self, z):
        for rid, path in self.rels_map.items():
            if "diagrams/data" in path and path in z.namelist():
                try:
                    xml_content = z.read(path)
                    self.smartart_data[rid] = self._parse_smartart_xml(xml_content)
                except:
                    pass

            if "charts/chart" in path and path in z.namelist():
                try:
                    xml_content = z.read(path)
                    self.chart_data[rid] = self._parse_chart_xml(xml_content)
                except:
                    pass

    def _parse_smartart_xml(self, xml_content):
        root = ET.fromstring(xml_content)
        texts = []
        for t in root.findall(".//dgm:t", NS):
            for at in t.findall(".//a:t", NS):
                if at.text:
                    texts.append(at.text)
        return " | ".join(texts)

    def _parse_chart_xml(self, xml_content):
        root = ET.fromstring(xml_content)
        info = []
        title = root.find(".//c:title//a:t", NS)
        if title is not None and title.text:
            info.append(f"Title: {title.text}")

        for ser in root.findall(".//c:ser", NS):
            ser_texts = []
            ser_name = ser.find(".//c:tx//c:v", NS)
            if ser_name is not None and ser_name.text:
                ser_texts.append(f"[{ser_name.text}]")

            cats = [v.text for v in ser.findall(".//c:cat//c:v", NS) if v.text]
            vals = [v.text for v in ser.findall(".//c:val//c:v", NS) if v.text]

            if cats and vals:
                data_pairs = [f"{c}={v}" for c, v in zip(cats, vals)]
                ser_texts.append(", ".join(data_pairs))
            elif vals:
                ser_texts.append(", ".join(vals))

            if ser_texts:
                info.append(" ".join(ser_texts))
        return " | ".join(info)

    def _extract_images(self, z):
        if os.path.exists(self.image_output_dir):
            shutil.rmtree(self.image_output_dir)
        os.makedirs(self.image_output_dir)
        count = 0
        for file_info in z.infolist():
            if file_info.filename.startswith(
                "word/media/"
            ) and not file_info.filename.endswith("/"):
                ext = os.path.splitext(file_info.filename)[1]
                count += 1
                new_filename = f"image_{count:02d}{ext}"
                target_path = os.path.join(self.image_output_dir, new_filename)
                with open(target_path, "wb") as f:
                    f.write(z.read(file_info))
                self.media_files[file_info.filename] = new_filename

    def _parse_styles_xml(self):
        root = ET.fromstring(self.styles_xml)
        for style in root.findall("w:style", NS):
            style_id = style.get(f"{{{NS['w']}}}styleId")
            rPr = style.find("w:rPr", NS)
            props = {}
            if rPr is not None:
                props = self._extract_run_properties(rPr)
            pPr = style.find("w:pPr", NS)
            if pPr is not None:
                bg_val = self._get_bg_color(pPr)
                if bg_val:
                    props["bg"] = bg_val
            if props:
                self.styles_map[style_id] = props

    def _extract_run_properties(self, rPr):
        props = {}
        color = rPr.find("w:color", NS)
        if color is not None:
            val = color.get(f"{{{NS['w']}}}val")
            if val and val != "auto":
                props["color"] = val
        sz = rPr.find("w:sz", NS)
        if sz is not None:
            val = sz.get(f"{{{NS['w']}}}val")
            if val:
                try:
                    props["size"] = str(float(val) / 2) + "pt"
                except:
                    pass
        bg_val = self._get_bg_color(rPr)
        if bg_val:
            props["bg"] = bg_val
        if rPr.find("w:b", NS) is not None:
            props["bold"] = True
        if rPr.find("w:bdr", NS) is not None:
            props["border"] = True
        return props

    def _get_bg_color(self, element_pr):
        shd = element_pr.find("w:shd", NS)
        hl = element_pr.find("w:highlight", NS)
        bg_val = None
        if shd is not None:
            fill = shd.get(f"{{{NS['w']}}}fill")
            color = shd.get(f"{{{NS['w']}}}color")
            theme_fill = shd.get(f"{{{NS['w']}}}themeFill")
            if fill and fill not in ["auto", "FFFFFF", "000000", "nil"]:
                bg_val = fill
            elif color and color not in ["auto", "FFFFFF", "000000", "nil"]:
                bg_val = color
            elif theme_fill:
                bg_val = f"Theme:{theme_fill}"
        if hl is not None:
            val = hl.get(f"{{{NS['w']}}}val")
            if val and val not in ["none", "nil"]:
                bg_val = f"HL:{val}"
        return bg_val

    def _detect_default_styles(self):
        root = ET.fromstring(self.doc_xml)
        body = root.find("w:body", NS)
        colors, sizes, bgs, styles = Counter(), Counter(), Counter(), Counter()
        for r in body.iter(f"{{{NS['w']}}}r"):
            props = self._resolve_run_properties(r)
            colors[props.get("color", "auto")] += 1
            sizes[props.get("size", "auto")] += 1
            bgs[props.get("bg", "none")] += 1
            rPr = r.find("w:rPr", NS)
            if rPr is not None:
                rStyle = rPr.find("w:rStyle", NS)
                if rStyle is not None:
                    styles[rStyle.get(f"{{{NS['w']}}}val")] += 1
                else:
                    styles["none"] += 1
            else:
                styles["none"] += 1
        if colors:
            self.default_styles["color"] = colors.most_common(1)[0][0]
        if sizes:
            self.default_styles["size"] = sizes.most_common(1)[0][0]
        if bgs:
            self.default_styles["bg"] = bgs.most_common(1)[0][0]
        if styles:
            self.default_styles["style"] = styles.most_common(1)[0][0]

    def _resolve_run_properties(self, r_element, paragraph_props=None):
        props = {}
        if paragraph_props:
            props.update(paragraph_props)
        rPr = r_element.find("w:rPr", NS)
        if rPr is not None:
            rStyle = rPr.find("w:rStyle", NS)
            if rStyle is not None:
                style_id = rStyle.get(f"{{{NS['w']}}}val")
                if style_id in self.styles_map:
                    props.update(self.styles_map[style_id])
        if rPr is not None:
            direct_props = self._extract_run_properties(rPr)
            props.update(direct_props)
        return props

    def _generate_map(self):
        root = ET.fromstring(self.doc_xml)
        body = root.find("w:body", NS)
        lines = []
        lines.append(f"--- Word Structure Map: {os.path.basename(self.docx_path)} ---")
        lines.append(
            "このテキストはWord文書の構造、スタイル、画像の配置を示したマップです。"
        )
        lines.append(
            f"画像ファイルは '{self.image_output_dir}/' フォルダに抽出されています。"
        )
        lines.append("")
        lines.append("【凡例とデフォルト設定】")
        lines.append("- [HEADING] や [TABLE] などのタグは文書構造を表します。")
        lines.append(
            "- {{属性| テキスト}} の形式は、特定のスタイルが適用された箇所です。"
        )
        lines.append("- [DRAWING/SHAPE] は図形、SmartArt、グラフなどを表します。")
        def_c, def_s, def_b, def_st = (
            self.default_styles["color"],
            self.default_styles["size"],
            self.default_styles["bg"],
            self.default_styles["style"],
        )
        lines.append("- 以下の属性は「文書の標準スタイル」として省略されています:")
        lines.append(f"    - 文字色 (Color): {def_c if def_c != 'auto' else '自動/黒'}")
        lines.append(
            f"    - サイズ (Size): {def_s if def_s != 'auto' else '自動/標準'}"
        )
        lines.append(f"    - 背景色 (BG): {def_b if def_b != 'none' else 'なし'}")
        if def_st and def_st != "none":
            lines.append(f"    - スタイル (Style): {def_st}")
        lines.append("--------------------------------------------------")
        lines.append("")
        for child in body:
            tag_name = child.tag.split("}")[-1]
            if tag_name == "p":
                text = self._parse_paragraph(child)
                if text:
                    lines.append(text)
            elif tag_name == "tbl":
                lines.append("[TABLE START]")
                lines.extend(self._parse_table(child))
                lines.append("[TABLE END]")
        return "\n".join(lines)

    def _parse_paragraph(self, p_element, in_shape=False):
        text_parts = []
        tags = []
        paragraph_props = {}
        pPr = p_element.find("w:pPr", NS)
        if pPr is not None:
            pStyle = pPr.find("w:pStyle", NS)
            if pStyle is not None:
                style_val = pStyle.get(f"{{{NS['w']}}}val")
                if style_val and ("Heading" in style_val or "Title" in style_val):
                    tags.append(f"[{style_val.upper()}]")
            numPr = pPr.find("w:numPr", NS)
            if numPr is not None:
                tags.append("[LIST_ITEM]")
            bg_val = self._get_bg_color(pPr)
            if bg_val:
                paragraph_props["bg"] = bg_val

        for child in p_element:
            tag_name = child.tag.split("}")[-1]
            if tag_name == "r":
                r_content = self._parse_run(child, paragraph_props)
                if r_content:
                    text_parts.append(r_content)
            elif tag_name == "hyperlink":
                hl_text = []
                for r in child.findall("w:r", NS):
                    r_content = self._parse_run(r, paragraph_props)
                    if r_content:
                        hl_text.append(r_content)
                if hl_text:
                    text_parts.append(f"[LINK: {''.join(hl_text)}]")
            elif tag_name == "smartTag":
                for r in child.findall("w:r", NS):
                    r_content = self._parse_run(r, paragraph_props)
                    if r_content:
                        text_parts.append(r_content)

        full_text = "".join(text_parts).strip()
        if not full_text and not tags:
            return None
        return f"{' '.join(tags)} {full_text}".strip()

    def _parse_run(self, r_element, paragraph_props):
        parts = []

        # 1. Text (w:t)
        # Note: 標準的なWordファイルでは w:r の中に w:t や w:drawing が並列することは稀だが、
        # 念のため既存ロジック通り w:t は個別に処理
        t = r_element.find("w:t", NS)
        if t is not None and t.text:
            run_text = t.text
            props = self._resolve_run_properties(r_element, paragraph_props)
            style_infos = []
            rPr = r_element.find("w:rPr", NS)
            if rPr is not None:
                rStyle = rPr.find("w:rStyle", NS)
                if rStyle is not None:
                    s_val = rStyle.get(f"{{{NS['w']}}}val")
                    if s_val and s_val != self.default_styles["style"]:
                        style_infos.append(f"Style:{s_val}")
            c_val = props.get("color", "auto")
            if c_val != self.default_styles["color"]:
                if c_val != "auto":
                    style_infos.append(f"C:{c_val}")
            s_val = props.get("size", "auto")
            if s_val != self.default_styles["size"]:
                if s_val != "auto":
                    style_infos.append(f"S:{s_val}")
            bg_val = props.get("bg", "none")
            if bg_val != self.default_styles["bg"]:
                if bg_val != "none":
                    style_infos.append(f"BG:{bg_val}")
            if props.get("bold"):
                style_infos.append("Bold")
            if props.get("border"):
                style_infos.append("BOX")
            if rPr is not None:
                u = rPr.find("w:u", NS)
                if u is not None:
                    val_attr = f"{{{NS['w']}}}val"
                    u_val = u.get(val_attr)
                    if u_val and u_val != "none":
                        style_infos.append(f"UL:{u_val}")
            if style_infos:
                style_str = " ".join(style_infos)
                run_text = f"{{{{{style_str}| {run_text}}}}}"
            parts.append(run_text)

        # 2. Drawing Objects (AlternateContent aware)
        # 直接 findall('.//w:drawing') するのではなく、AlternateContentを考慮して走査
        for child in r_element:
            tag = child.tag
            if tag == f"{{{NS['mc']}}}AlternateContent":
                # Choiceを優先
                choice = child.find(f"{{{NS['mc']}}}Choice", NS)
                if choice is not None:
                    # Choiceの中身（Drawingなど）を処理
                    for sub_child in choice:
                        if sub_child.tag == f"{{{NS['w']}}}drawing":
                            parts.extend(
                                self._extract_drawing_content_robust(sub_child)
                            )
                        elif sub_child.tag == f"{{{NS['w']}}}pict":
                            parts.extend(
                                self._extract_drawing_content_robust(sub_child)
                            )
                else:
                    # Choiceがない場合はFallback（稀）
                    fallback = child.find(f"{{{NS['mc']}}}Fallback", NS)
                    if fallback is not None:
                        for sub_child in fallback:
                            if sub_child.tag == f"{{{NS['w']}}}drawing":
                                parts.extend(
                                    self._extract_drawing_content_robust(sub_child)
                                )
                            elif sub_child.tag == f"{{{NS['w']}}}pict":
                                parts.extend(
                                    self._extract_drawing_content_robust(sub_child)
                                )

            elif tag == f"{{{NS['w']}}}drawing":
                # AlternateContentの外にある直接のDrawing
                parts.extend(self._extract_drawing_content_robust(child))

            elif tag == f"{{{NS['w']}}}pict":
                # AlternateContentの外にある直接のPict
                parts.extend(self._extract_drawing_content_robust(child))

        return "".join(parts)

    def _extract_drawing_content_robust(self, parent_element):
        extracted = []
        info_tags = []

        # 1. 形状情報のヒントとデータリンク収集
        # SmartArt Link
        dgm_rel = parent_element.find(".//dgm:relIds", NS)
        if dgm_rel is not None:
            rid = dgm_rel.get(f"{{{NS['r']}}}dm")
            if rid and rid in self.smartart_data:
                info_tags.append("SMARTART")
                extracted.append(f"\n[SmartArt Data: {self.smartart_data[rid]}]")

        # Chart Link
        chart = parent_element.find(".//c:chart", NS)
        if chart is not None:
            rid = chart.get(f"{{{NS['r']}}}id")
            if rid and rid in self.chart_data:
                info_tags.append("CHART")
                extracted.append(f"\n[Chart Data: {self.chart_data[rid]}]")

        # 形状タイプ
        for geom in parent_element.findall(".//a:prstGeom", NS):
            prst = geom.get("prst")
            if prst:
                info_tags.append(f"Shape:{prst}")

        # VML ShapeType
        for vshape in parent_element.findall(".//v:shape", NS):
            stype = vshape.get("type")
            if stype:
                info_tags.append(f"VML:{stype}")

        # 2. 画像参照
        for blip in parent_element.findall(".//a:blip", NS):
            embed_id = blip.get(f"{{{NS['r']}}}embed")
            if embed_id and embed_id in self.rels_map:
                zip_path = self.rels_map[embed_id]
                if zip_path in self.media_files:
                    filename = self.media_files[zip_path]
                    extracted.append(f"\n[IMAGE REF: {filename}]")

        # VML画像
        for idata in parent_element.findall(".//v:imagedata", NS):
            rid = idata.get(f"{{{NS['r']}}}id")
            if rid and rid in self.rels_map:
                zip_path = self.rels_map[rid]
                if zip_path in self.media_files:
                    filename = self.media_files[zip_path]
                    extracted.append(f"\n[IMAGE REF: {filename}]")

        # 3. テキスト抽出 (再帰)
        paragraphs = parent_element.findall(".//w:p", NS)

        has_text_content = False
        drawing_text_parts = []
        if paragraphs:
            for p in paragraphs:
                text = self._parse_paragraph(p, in_shape=True)
                if text:
                    drawing_text_parts.append(text)
                    has_text_content = True

        tag_str = " ".join(list(set(info_tags)))

        if tag_str or has_text_content or extracted:
            header = f"\n[DRAWING: {tag_str}]" if tag_str else "\n[DRAWING]"
            extracted.insert(0, header)
            if drawing_text_parts:
                extracted.append(f" Content: {' | '.join(drawing_text_parts)}")
            extracted.append("\n")

        return extracted

    def _parse_table(self, tbl_element):
        rows = []
        for tr in tbl_element.findall("w:tr", NS):
            cells = []
            for tc in tr.findall("w:tc", NS):
                cell_texts = []
                for p in tc.findall("w:p", NS):
                    text = self._parse_paragraph(p)
                    if text:
                        cell_texts.append(text)
                cells.append("<br>".join(cell_texts))
            rows.append("| " + " | ".join(cells) + " |")
        return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Word Map for LLM")
    parser.add_argument("filename", nargs="?", help="Target .docx filename")
    parser.add_argument(
        "--img-dir",
        default="extracted_images",
        help="Directory to save extracted images",
    )
    args = parser.parse_args()

    target_file = args.filename
    if not target_file:
        docx_files = [
            f for f in os.listdir(".") if f.endswith(".docx") and not f.startswith("~$")
        ]
        if docx_files:
            target_file = docx_files[0]
            print(f"No file specified. Using found file: {target_file}")
        else:
            print("No .docx files found in the current directory.")
            sys.exit(1)

    print(f"--- Analyzing: {target_file} ---")
    mapper = WordMapper(target_file, image_output_dir=args.img_dir)
    result = mapper.analyze()
    print(result)
    print("--------------------------------------------------")
