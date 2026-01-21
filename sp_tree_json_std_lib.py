"""
LLM共有用プロジェクトダンプツール (All-in-One Version)
==================================================

プロジェクトのディレクトリ構造とファイルの中身を、LLM（ChatGPT, Claude, Gemini等）に
共有しやすい形式（軽量JSON）で出力するスクリプトです。

【特徴】
1. ポータビリティ: 標準ライブラリのみで動作（最小構成）。
2. 高機能モード: ライブラリ追加で「正確なコード抽出」「依存関係解決」「トークン計算」が有効化。
3. 柔軟な出力: 
   - 「全ファイルのフルコンテキスト」
   - 「ディレクトリ構造のみ」
   - 「ファイル構成図（中身なし）」
   など、目的に応じて出力を調整可能。
4. Git連携: ステージング済みファイルや変更分のみを抽出可能。

==================================================

【セットアップ (推奨)】
以下のコマンドでライブラリをインストールすると、全機能が解放されます。
(インストールしなくても標準機能で動作します)

    # 通常のpip
    pip install tree-sitter tree-sitter-languages networkx tiktoken pyperclip

    # uvを使用している場合
    uv pip install tree-sitter tree-sitter-languages networkx tiktoken pyperclip

【各ライブラリの役割】
- tree-sitter系 : 関数/クラス定義を文法レベルで正確に抽出 (Focusモード用)
- networkx      : import文を解析し、依存関係にあるファイルを自動収集
- tiktoken      : 出力結果の正確なトークン数を計算して表示
- pyperclip     : 出力結果をクリップボードに自動コピー

==================================================

【オプション一覧】

1. 入出力・基本設定
  -p, --path PATH             処理対象のルートディレクトリ (デフォルト: ".")
  -o, --outfile FILE          結果を指定ファイルに出力 (未指定時は標準出力)
  -c, --copy                  結果をクリップボードにコピー (要 pyperclip)
  --debug                     デバッグログを表示

2. 構造・プレビュー制御 (出力内容の調整)
  --directories-only          ファイルを含めず、ディレクトリ構造のみを出力
  --include-non-preview       プレビュー対象外のファイルもツリーに表示する (中身は空文字)
                              ※ これをONにすると「ファイル一覧図」が作れます
  --preview-exts EXTS...      中身をテキストとして読み込む拡張子を指定
                              (デフォルト: .py .md .txt .json .js .ts .html .css 等)
  --preview-lines INT         1ファイルあたりの最大読み込み行数 (デフォルト: 2000)
  --max-preview-size-mb FLOAT 1ファイルあたりの最大サイズ(MB) (デフォルト: 1.0)

3. フィルタリング (除外・Git)
  -e, --exclude PATTERNS...   除外するファイル/フォルダのパターン (例: "*.log" "tmp*")
                              ※ デフォルトで .git, node_modules, venv, __pycache__ 等は除外済
                              ※ 追加指定してもデフォルト設定は維持されます
  --git-filter MODE           Gitの状態に基づいて絞り込み
                              [モード]
                              - None     : フィルタなし (デフォルト)
                              - Tracked  : Git管理下のファイルのみ
                              - Staged   : git add 済みのファイルのみ (レビュー用)
                              - Modified : 変更があるファイルのみ (作業ログ用)

4. Focusモード (特定コードの切り抜き)
  -f, --focus KEYWORD         指定したキーワード(関数名/クラス名)に関連するコードのみ抽出
                              ※ Tree-sitter導入時は文法レベルで正確に抽出
  --resolve-deps              Focusモード時、依存関係(import)にあるファイルも含める
                              (要 networkx)

5. その他
  --model NAME                トークン計算に使用するモデル名 (デフォルト: gpt-4o)

==================================================

【コマンド使用例】

1. 基本的な使い方
   # カレントディレクトリの全コードをクリップボードにコピー（最も一般的）
   python sp_tree_json_std_lib.py --copy

   # 結果をファイルに保存
   python sp_tree_json_std_lib.py -o context.json

   # 標準出力に表示（パイプ処理などに）
   python sp_tree_json_std_lib.py

2. プロジェクト構造の把握（トークン節約）
   # ディレクトリ構造のみを表示（ファイル名は非表示）
   # -> フォルダ構成だけをAIに伝えたい時に最適
   python sp_tree_json_std_lib.py --directories-only

   # 全ファイル名を表示するが、中身はすべて空にする
   # -> 「どこにどんなファイルがあるか」という地図をAIに渡す用（トークン超軽量）
   python sp_tree_json_std_lib.py --preview-exts --include-non-preview

   # Pythonファイルだけ中身を表示し、画像やログなどはファイル名のみ表示
   # -> 重要なコードだけ読ませて、他は存在だけ伝えたい場合
   python sp_tree_json_std_lib.py --preview-exts .py --include-non-preview

3. Gitワークフローとの連携
   # 「git add」済みのファイルのみ出力
   # -> コミットメッセージの作成や、コードレビュー依頼に最適
   python sp_tree_json_std_lib.py --git-filter Staged --copy

   # 変更があったファイル（未ステージ含む）のみ出力
   # -> 作業中の内容について相談したい時
   python sp_tree_json_std_lib.py --git-filter Modified

   # Git管理下のファイルのみ出力（ゴミファイルや未管理ファイルを除外）
   python sp_tree_json_std_lib.py --git-filter Tracked

4. Focusモード（特定の機能・コードをピンポイント抽出）
   # 関数名 "login_user" の定義部分だけを抽出
   python sp_tree_json_std_lib.py --focus "login_user"

   # クラス "User" と、それが依存(import)しているファイル群もセットで抽出
   # -> 機能改修の影響範囲を調査する時に強力（要 networkx）
   python sp_tree_json_std_lib.py --focus "User" --resolve-deps

   # "FIXME" という単語を含む箇所を抽出してコピー
   python sp_tree_json_std_lib.py --focus "FIXME" --copy

5. フィルタリングとサイズ制御
   # ログファイル、一時フォルダ、特定の設定ファイルを除外
   python sp_tree_json_std_lib.py --exclude "*.log" "temp*" "secret.yaml"

   # 1ファイルあたりの読み込みを先頭500行までに制限（巨大ファイル対策）
   python sp_tree_json_std_lib.py --preview-lines 500

   # .py と .md だけ中身を表示し、他は除外（ツリーにも出さない）
   python sp_tree_json_std_lib.py --preview-exts .py .md
"""

import os
import sys
import json
import argparse
import subprocess
import fnmatch
import re
import ast
from pathlib import Path
from typing import List, Set, Optional, Dict
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# Optional Dependencies
# ==========================================
HAS_TIKTOKEN = False
HAS_PYPERCLIP = False
HAS_NETWORKX = False
HAS_TREESITTER = False

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    pass

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    pass

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    pass

try:
    from tree_sitter_languages import get_parser
    HAS_TREESITTER = True
except ImportError:
    pass

# ==========================================
# Tree-sitter Mapping
# ==========================================
TREESITTER_EXT_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cs': 'c_sharp',
    '.rb': 'ruby',
    '.php': 'php',
    '.html': 'html',
}

# ==========================================
# Config
# ==========================================
DEFAULT_EXCLUDES = [
    'venv*', '.venv', '.env', '.git', 'node_modules', '__pycache__', '.vscode',
    '_deps', '*.dir', 'x64', '.cache', '.history', '*.pyc', '*.class', 
    'sp_tree_json_std_lib.py', '*.egg-info', 'dist', 'build',
    ".ruff_cache", ".history", ".json", ".DS_Store", "package-lock.json", "yarn.lock"
]

DEFAULT_PREVIEW_EXTS = [
    '.md', '.py', '.txt', '.json', '.yaml', '.yml', '.c', '.h', '.cpp', '.hpp', '.java', 
    '.html', '.js', '.jsx', '.ts', '.tsx', '.sh', '.bat', '.ps1', '.css', '.sql', '.rs', '.go',
    '.dockerfile', 'Dockerfile', '.toml', '.ini'
]

def parse_args():
    parser = argparse.ArgumentParser(description="LLM共有用プロジェクトダンプツール")
    
    parser.add_argument('--path', '-p', default='.', help='対象ディレクトリパス')
    parser.add_argument('--exclude', '-e', nargs='*', default=DEFAULT_EXCLUDES, help='除外パターン')
    parser.add_argument('--outfile', '-o', default='', help='出力先ファイルパス')
    parser.add_argument('--directories-only', action='store_true', help='ファイルを含めずディレクトリ構造のみ出力')
    parser.add_argument('--include-non-preview', action='store_true', help='プレビュー対象外のファイルもツリーには表示する（中身は省略）')
    
    parser.add_argument('--preview-exts', nargs='*', default=DEFAULT_PREVIEW_EXTS, help='対象拡張子')
    parser.add_argument('--preview-lines', type=int, default=2000, help='最大行数')
    parser.add_argument('--max-preview-size-mb', type=float, default=1.0, help='最大サイズ(MB)')
    
    parser.add_argument('--git-filter', choices=['None', 'Tracked', 'Staged', 'Modified'], default='None', help='Git状態フィルタ')
    
    parser.add_argument('--focus', '-f', default=None, help='指定したキーワード(関数名・クラス名)を抽出')
    parser.add_argument('--resolve-deps', action='store_true', help='Focus時、依存ファイルも含める (要networkx)')
    
    parser.add_argument('--copy', '-c', action='store_true', help='クリップボードにコピー (要pyperclip)')
    parser.add_argument('--model', default='gpt-4o', help='トークン計算モデル (要tiktoken)')
    parser.add_argument('--debug', action='store_true', help='デバッグログ')

    return parser.parse_args()

def log_debug(msg: str, is_debug: bool):
    if is_debug:
        print(f"[DEBUG] {msg}", file=sys.stderr)

# ==========================================
# 1. Dependency Analysis (Graph Logic)
# ==========================================
def extract_imports(file_path: Path, content: str) -> Set[str]:
    """簡易的なImport抽出 (Regex & AST)"""
    imports = set()
    ext = file_path.suffix.lower()

    if ext == '.py':
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.add(n.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except Exception:
            pass
    else:
        # 簡易Regex (JS/TS/C/Rust等)
        patterns = [
            r'import\s+.*\s+from\s+[\'"](.+)[\'"]', 
            r'require\s*\([\'"](.+)[\'"]\)',
            r'#include\s*[<"](.+)[>"]',
            r'use\s+(.+);',
        ]
        for pat in patterns:
            for m in re.findall(pat, content):
                imports.add(os.path.basename(m).split('.')[0])
    return imports

def build_dependency_graph(file_map: Dict[Path, str], is_debug: bool):
    if not HAS_NETWORKX:
        return None
    G = nx.DiGraph()
    name_to_path = {p.stem: p for p in file_map.keys()}
    
    log_debug("Building dependency graph...", is_debug)
    for path, content in file_map.items():
        for name in extract_imports(path, content):
            if name in name_to_path and name_to_path[name] != path:
                G.add_edge(path, name_to_path[name])
    return G

def get_related_files(target_paths: List[Path], G) -> Set[Path]:
    if G is None:
        return set(target_paths)
    related = set(target_paths)
    for p in target_paths:
        if p in G:
            related.update(nx.descendants(G, p))
    return related

# ==========================================
# 2. Code Extraction (Tree-sitter)
# ==========================================
def extract_code_block_treesitter(content: str, ext: str, keyword: str) -> Optional[str]:
    """Tree-sitterを使用して、多言語対応で関数/クラス定義を抽出する"""
    if not HAS_TREESITTER:
        return None
    
    lang_name = TREESITTER_EXT_MAP.get(ext)
    if not lang_name:
        return None

    try:
        parser = get_parser(lang_name)
        content_bytes = content.encode('utf-8')
        tree = parser.parse(content_bytes)
        
        extracted_parts = []
        
        # 定義とみなすノードタイプのキーワード
        DEF_KEYWORDS = {'function', 'method', 'class', 'struct', 'impl', 'interface', 'declaration', 'definition'}
        visited = set()

        def visit(node):
            if node.id in visited:
                return
            visited.add(node.id)

            is_def_type = any(k in node.type for k in DEF_KEYWORDS)
            
            if is_def_type:
                name_node = node.child_by_field_name('name')
                if name_node:
                    node_name = content_bytes[name_node.start_byte : name_node.end_byte].decode('utf-8')
                    if keyword == node_name:
                        code_text = content_bytes[node.start_byte : node.end_byte].decode('utf-8')
                        extracted_parts.append(code_text)
                        return # このノード以下は探索不要

            for child in node.children:
                visit(child)

        visit(tree.root_node)

        if extracted_parts:
            return "\n\n".join(extracted_parts)
        return None

    except Exception:
        return None

# ==========================================
# 3. Code Extraction (Standard Logic)
# ==========================================
def extract_code_block_ast(code: str, keyword: str) -> Optional[str]:
    """Python AST fallback"""
    try:
        tree = ast.parse(code)
        lines = code.splitlines()
        extracted = []
        
        class Visitor(ast.NodeVisitor):
            def _check(self, node):
                if hasattr(node, 'name') and keyword in node.name:
                    start = node.lineno - 1
                    end = node.end_lineno
                    if getattr(node, 'decorator_list', []):
                         start = min(d.lineno - 1 for d in node.decorator_list)
                    extracted.append("\n".join(lines[start:end]))
            
            def visit_FunctionDef(self, n):
                self._check(n)
                self.generic_visit(n)
                
            def visit_AsyncFunctionDef(self, n):
                self._check(n)
                self.generic_visit(n)
                
            def visit_ClassDef(self, n):
                self._check(n)
                self.generic_visit(n)

        Visitor().visit(tree)
        return "\n\n".join(extracted) if extracted else None
    except Exception:
        return None

def extract_code_block_braces(code: str, keyword: str) -> Optional[str]:
    """C-style fallback"""
    lines = code.splitlines()
    extracted = []
    for i, line in enumerate(lines):
        if keyword in line and '{' in line:
            current_block = []
            balance, started = 0, False
            for j in range(i, len(lines)):
                line_one = lines[j]
                current_block.append(line_one)
                balance += line_one.count('{') - line_one.count('}')
                if balance > 0:
                    started = True
                if started and balance == 0:
                    extracted.append("\n".join(current_block))
                    break
    return "\n\n".join(extracted) if extracted else None

# ==========================================
# 4. Main Workflow
# ==========================================
def get_git_files(root_path: Path, mode: str) -> Set[str]:
    files = set()
    cmds = []
    
    # -z オプションを追加して、エスケープを無効化（NULL文字区切りにする）
    if mode == 'Tracked':
        cmds = [['git', 'ls-files', '-z']]
    elif mode == 'Staged':
        cmds = [['git', 'diff', '--name-only', '--cached', '-z']]
    elif mode == 'Modified':
        cmds = [
            ['git', 'diff', '--name-only', '-z'],
            ['git', 'diff', '--name-only', '--cached', '-z'],
            ['git', 'ls-files', '--others', '--exclude-standard', '-z']
        ]
    
    for cmd in cmds:
        try:
            # -z を使う場合、encodingはそのままでOKだが、区切り処理を変える
            res = subprocess.run(cmd, cwd=root_path, capture_output=True, text=True, encoding='utf-8')
            if res.returncode == 0:
                # splitlines() ではなく split('\0') で分割する
                # 末尾に空文字が入ることがあるのでフィルタする
                for line in res.stdout.split('\0'):
                    if line.strip():
                        # Pathとして解決
                        files.add(str((root_path / line.strip()).resolve()))
        except Exception:
            pass
    return files

def should_exclude(name: str, excludes: List[str]) -> bool:
    for pattern in excludes:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False

def collect_files(root_path: Path, args, git_allowed) -> List[Path]:
    target_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # 除外ディレクトリのフィルタリング
        dirnames[:] = [d for d in dirnames if not should_exclude(d, args.exclude)]
        
        # ディレクトリ構造のみモードの場合はファイルを収集しない
        if args.directories_only:
            continue
        
        for f in filenames:
            # 除外ファイルのフィルタリング
            if should_exclude(f, args.exclude):
                continue
            
            f_path = Path(dirpath) / f
            ext = f_path.suffix.lower()
            
            # Gitフィルタリングチェック
            if git_allowed is not None and str(f_path.resolve()) not in git_allowed:
                continue

            # 【判定ロジック】
            # 1. プレビュー対象リストに入っている -> OK
            # 2. フラグ --include-non-preview がON -> OK
            if (ext in args.preview_exts) or args.include_non_preview:
                target_files.append(f_path)
                
    return target_files

def read_content(path: Path) -> Optional[str]:
    for enc in ['utf-8', 'cp932', 'latin-1']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    return None

def main():
    args = parse_args()
    if args.exclude != DEFAULT_EXCLUDES:
        args.exclude = list(set(args.exclude + DEFAULT_EXCLUDES))
    root_path = Path(args.path).resolve()
    
    # Check dependencies for debug
    if args.debug:
        log_debug(f"Tree-sitter: {'OK' if HAS_TREESITTER else 'Missing'}", True)
        log_debug(f"NetworkX:    {'OK' if HAS_NETWORKX else 'Missing'}", True)

    git_allowed = get_git_files(root_path, args.git_filter) if args.git_filter != 'None' else None
    all_files = collect_files(root_path, args, git_allowed)

    file_map = {}
    files_to_read = []

    # まず、ファイルを「読むもの」と「空で登録するもの」に振り分ける
    for fpath in all_files:
        ext = fpath.suffix.lower()
        if ext in args.preview_exts:
            files_to_read.append(fpath)
        else:
            # プレビュー対象外（--include-non-previewで入ったもの）は
            # 読み込まずに空文字をセットする
            file_map[fpath] = ""

    # 必要なファイルだけを並列読み込み（IOコスト削減）
    with ThreadPoolExecutor() as executor:
        results = executor.map(read_content, files_to_read)
        for fpath, content in zip(files_to_read, results):
            # 読み込み成功、かつサイズ制限内なら格納
            if content and len(content.encode('utf-8')) <= args.max_preview_size_mb * 1024 * 1024:
                file_map[fpath] = content
            else:
                # 読み込み失敗やサイズ超過時は空文字（存在は残す）
                file_map[fpath] = ""

    # Focus & Deps logic
    final_targets = set(file_map.keys())
    if args.focus:
        # Focusモード時の絞り込み
        focus_roots = [p for p, c in file_map.items() if args.focus in p.name or args.focus in c]
        
        if args.resolve_deps and HAS_NETWORKX:
            G = build_dependency_graph(file_map, args.debug)
            final_targets = get_related_files(focus_roots, G)
        else:
            final_targets = set(focus_roots)

    # Build Tree
    def build_tree(current_path):
        node = {"name": current_path.name}
        
        if current_path.is_dir():
            children = []
            try:
                for item in sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if should_exclude(item.name, args.exclude):
                        continue
                    
                    if item.is_dir():
                        child = build_tree(item)
                        
                        # ▼▼▼ 修正箇所1: 子ディレクトリを追加する条件を緩和 ▼▼▼
                        if child:
                            # ディレクトリのみモードなら、中身に関わらず追加
                            if args.directories_only:
                                children.append(child)
                            # 通常モードなら、中身がある場合のみ追加
                            elif child.get("children") or child.get("files_inside"):
                                children.append(child)
                                
                    elif item in final_targets:
                        # (ここは変更なし)
                        content = file_map[item]
                        if args.focus:
                            extracted = None
                            if HAS_TREESITTER:
                                extracted = extract_code_block_treesitter(content, item.suffix.lower(), args.focus)
                            if not extracted and item.suffix.lower() == '.py':
                                extracted = extract_code_block_ast(content, args.focus)
                            if not extracted:
                                extracted = extract_code_block_braces(content, args.focus)
                            if extracted:
                                content = extracted
                        
                        if content:
                            lines = content.splitlines()[:args.preview_lines]
                            preview_text = "\n".join(lines)
                        else:
                            preview_text = ""
                        children.append({"name": item.name, "preview": preview_text})

            except Exception:
                pass
            
            node["children"] = children
            node["files_inside"] = len(children) > 0
            
            # ▼▼▼ 修正箇所2: 自身を返す条件を緩和 ▼▼▼
            # ディレクトリのみモードなら、中身が空でも自身（ディレクトリ）を返す
            if args.directories_only:
                return node
            
            # 通常時は、中身がある場合のみ返す
            return node if node["files_inside"] else None
        
        return None


    root_node = build_tree(root_path)
    
    # Output
    if root_node:
        try:
            json_str = json.dumps(root_node, ensure_ascii=False, indent=None, separators=(',', ':'))
            
            # Token Count
            count = len(json_str) // 4
            if HAS_TIKTOKEN:
                try:
                    count = len(tiktoken.encoding_for_model(args.model).encode(json_str))
                except Exception:
                    pass
            print(f"[Tokens: {count:,}]", file=sys.stderr)

            if args.outfile:
                with open(args.outfile, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                print(f"Saved to {args.outfile}")
            
            # コピー指定がある場合の処理
            elif args.copy:
                if HAS_PYPERCLIP:
                    pyperclip.copy(json_str)
                    print(">> Copied to clipboard! <<", file=sys.stderr)
                else:
                    print(">> [ERROR] クリップボードへのコピーに失敗しました。", file=sys.stderr)
                    print(">> 必要なライブラリが見つかりません: pip install pyperclip", file=sys.stderr)
                    print(">> 代わりに標準出力に表示します:\n", file=sys.stderr)
                    print(json_str)

            # ファイル指定もコピー指定もない場合（標準出力）
            else:
                print(json_str)

        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
    else:
        print("No files matched.", file=sys.stderr)

if __name__ == "__main__":
    main()