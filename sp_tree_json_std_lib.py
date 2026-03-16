"""
LLM共有用プロジェクトダンプツール (All-in-One Version)
==================================================

プロジェクトのディレクトリ構造とファイルの中身を、LLM（ChatGPT, Claude, Gemini等）に
共有しやすい形式（軽量JSON / Markdown風）で出力するスクリプトです。

【特徴】
1. ポータビリティ: 標準ライブラリのみで動作（最小構成）。
2. 高機能モード: ライブラリ追加で「正確なコード抽出」「依存関係解決」「トークン計算」が有効化。
3. 柔軟な出力: 
   - 「全ファイルのフルコンテキスト（JSON / Markdown風テキスト）」
   - 「ディレクトリ構造のみ」
   - 「ファイル構成図（中身なし）」
   など、目的に応じて出力を調整可能。
4. Git連携: ステージング済みファイルや変更分のみを抽出可能。

【新機能】
1. 要約＆アウトライン抽出: ファイル全体ではなく、冒頭の要約（人間が記述したコメント）や、
   クラス・関数のシグネチャ（アウトライン）だけを抽出。ノートPCのローカル環境でもLLMのトークンを節約。
2. 自動タグ付け＆高速検索: AST(構文解析)とTF-IDF(自然言語処理)を組み合わせ、ファイルに自動でタグ付け。
   軽量BM25エンジンに加え、ONNXを用いたローカル・セマンティック検索（意味検索）を搭載。
   「こんな機能を作りたい・直したい」という曖昧な自然言語から該当ファイルを特定します。
3. Smart Context: 指定したファイルが依存（import）している別ファイルの要約/アウトラインを自動で紐付け。
   ハルシネーションを強力に防ぎます。
4. インタラクティブモード: 検索でヒットしたファイル一覧を見ながら、ファイルごとに
   「全文出力 / 要約のみ / アウトラインのみ / 除外」をキーボードで対話的に選択可能。
5. キャッシュ機構: パース・要約・タグ付けの結果を自動で `.context_cache.json` に保存。
   巨大なプロジェクトでも2回目以降の実行は一瞬で完了し、ノートPCのバッテリーとCPUに優しい設計です。

==================================================

【セットアップ (推奨)】
以下のコマンドでライブラリをインストールすると、全機能（構文解析、依存解決、意味検索等）が解放されます。
(標準ライブラリのみでも軽量版として動作します)

    # 通常のpip
    pip install tree-sitter tree-sitter-languages networkx tiktoken pyperclip onnxruntime tokenizers numpy

    # uvを使用している場合
    uv pip install tree-sitter tree-sitter-languages networkx tiktoken pyperclip onnxruntime tokenizers numpy

【各ライブラリの役割】
- tree-sitter系 : 関数/クラス定義を文法レベルで正確に抽出・自動タグ付け
- networkx      : import文を解析し、依存関係(Smart Context)を自動解決
- tiktoken      : トークン数の正確な計算
- pyperclip     : クリップボードへの自動コピー
- onnxruntime, tokenizers, numpy : 極小エンコーダーモデルによるローカルでの意味検索（セマンティック検索）

==================================================

【オプション一覧】

1. 入出力・基本設定
  -p, --path PATH             処理対象のルートディレクトリ (デフォルト: ".")
  -o, --outfile FILE          結果を指定ファイルに出力 (未指定時は標準出力)
  -c, --copy                  結果をクリップボードにコピー (要 pyperclip)
  --debug                     デバッグログを表示
  --tree                      tree構造で視覚的に表示（中身なし）
  --text                      Markdown風のテキスト形式で出力（トークン節約）

2. 抽出・軽量化モード (LLMコンテキスト最適化)
  --summary-only              ファイルの中身を省き、冒頭の「要約コメント」と「タグ」のみを出力する
  --outline                   ファイルの中身を省き、クラスや関数のシグネチャ（アウトライン）のみを出力する
  --full FILES...             全体を要約出力にする場合でも、指定したファイル名を含む場合は詳細(全文)を出力する
  --interactive, -i           対話モード: 抽出されたファイルごとに「全文/要約/アウトライン/除外」を個別に選択する
  --smart-context             依存先ファイルを自動検出し、アウトライン形式でコンテキストに付与する (要 networkx)

3. 自然言語検索 ＆ タグ検索
  -s, --search QUERY          自然言語で「作りたい・直したい機能」を検索し、関連ファイルを出力する（BM25アルゴリズム）
  --semantic-search           ONNXを用いたローカルでの意味検索（セマンティック検索）を有効化 (要 onnxruntime)
  --search-full               検索対象を「要約+タグ」だけでなく、ファイル全体（全文）に拡張する
  --top-k INT                 検索時に関連度の高い上位N件のみを抽出する (デフォルト: 5)
  --tag TAGS...               指定したタグを完全に含むファイルのみを厳密に抽出する
  --vocab-file FILE           プロジェクト全体の共通タグ(ドメイン用語)を抽出するためのファイル (デフォルト: README.md)
  --dry-run                   ファイルを出力せず、検索や抽出の結果（対象ファイル一覧とタグ）のみをターミナルに表示する

4. 構造・プレビュー制御 (出力内容の調整)
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

  --use-gitignore            .gitignoreの記述を解析し、除外リストに追加されます。

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

   # Markdown形式でクリップボードにコピー (JSONよりトークン数を約10%節約)
   python sp_tree_json_std_lib.py --text --copy

   # 結果をファイルに保存 (JSON形式 / Markdown形式)
   python sp_tree_json_std_lib.py -o context.json

   # 結果をファイルに保存 (Markdown形式)
   python sp_tree_json_std_lib.py --text -o context.md

2. AI支援・検索機能の活用（作りたい・変更したい機能から探す）
   # 「ユーザーログイン処理の不具合を直したい」という意図から関連ファイルを探し、
   # インタラクティブモードでどれをLLMに渡すか選ぶ（ONNX意味検索を使用）
   python sp_tree_json_std_lib.py -s "ユーザーのログイン処理の不具合修正" --semantic-search --interactive --text --copy

   # 検索結果の上位3件の「要約」と、そのファイルが依存している別ファイルの「アウトライン」をセットで取得
   python sp_tree_json_std_lib.py -s "データベースへの保存処理" --top-k 3 --smart-context --text --copy

   # 全文検索を用いて、「API」と「認証」に関連するファイルを探し、結果だけをプレビュー（出力しない）
   python sp_tree_json_std_lib.py -s "API 認証" --search-full --dry-run

3. タグや抽出・軽量化モードの活用
   # 指定したタグ（例: auth, api）を持つファイルだけを抽出し、クリップボードにコピー
   python sp_tree_json_std_lib.py --tag auth api --copy

   # プロジェクト全体の「関数やクラスの定義一覧（アウトライン）」だけを出力（トークン超軽量化）
   python sp_tree_json_std_lib.py --outline --copy

   # 全ファイルは「要約」だけ出力しつつ、"main.py" と "config.py" だけは中身を「全文」出力する
   python sp_tree_json_std_lib.py --summary-only --full main.py config.py --copy

4. プロジェクト構造の把握（トークン節約）
   # ディレクトリ構造のみを表示（ファイル名は非表示）
   # -> フォルダ構成だけをAIに伝えたい時に最適
   python sp_tree_json_std_lib.py --directories-only

   # 全ファイル名を表示するが、中身はすべて空にする
   # -> 「どこにどんなファイルがあるか」という地図をAIに渡す用（トークン超軽量）
   python sp_tree_json_std_lib.py --preview-exts --include-non-preview

   # Pythonファイルだけ中身を表示し、画像やログなどはファイル名のみ表示
   # -> 重要なコードだけ読ませて、他は存在だけ伝えたい場合
   python sp_tree_json_std_lib.py --preview-exts .py --include-non-preview

5. Gitワークフローとの連携
   # 「git add」済みのファイルのみ出力
   # -> コミットメッセージの作成や、コードレビュー依頼に最適
   python sp_tree_json_std_lib.py --git-filter Staged --copy

   # 変更があったファイル（未ステージ含む）のみ出力
   # -> 作業中の内容について相談したい時
   python sp_tree_json_std_lib.py --git-filter Modified

   # Git管理下のファイルのみ出力（ゴミファイルや未管理ファイルを除外）
   python sp_tree_json_std_lib.py --git-filter Tracked

6. Focusモード（特定の機能・コードをピンポイント抽出）
   # 関数名 "login_user" の定義部分だけを抽出
   python sp_tree_json_std_lib.py --focus "login_user"

   # クラス "User" と、それが依存(import)しているファイル群もセットで抽出
   # -> 機能改修の影響範囲を調査する時に強力（要 networkx）
   python sp_tree_json_std_lib.py --focus "User" --resolve-deps

   # ファイル名で絞り込み（utils.py の中の save 関数だけ抽出）
   python sp_tree_json_std_lib.py --focus "utils.py:save"

   # .gitignoreの内容を除外し、結果をクリップボードに持つ。
   python sp_tree_json_std_lib.py --use-gitignore --copy

   # scrフォルダのmainがファイル名、main関数などが入っているファイルの関係ファイルを持ってくる
   python sp_tree_json_std_lib.py --focus "scr:main" --resolve-deps -o result.json

   # "FIXME" という単語を含む箇所を抽出してコピー
   python sp_tree_json_std_lib.py --focus "FIXME" --copy

7. フィルタリングとサイズ制御
   # ログファイル、一時フォルダ、特定の設定ファイルを除外
   python sp_tree_json_std_lib.py --exclude "*.log" "temp*" "secret.yaml"

   # 1ファイルあたりの読み込みを先頭500行までに制限（巨大ファイル対策）
   python sp_tree_json_std_lib.py --preview-lines 500

   # .py と .md だけ中身を表示し、他は除外（ツリーにも出さない）
   python sp_tree_json_std_lib.py --preview-exts .py .md

   # フィルタ(-e)で指定されたもの以外、全てのファイル・フォルダをツリー表示
   # 中身の読み込みは発生しません
   python sp_tree_json_std_lib.py --tree

   # ファイルを隠してフォルダのみ表示
   python sp_tree_json_std_lib.py --tree --directories-only

   # 複雑な除外指定の例
   python .\sp_tree_json_std_lib.py -p "Path" -e *.sql *.md *.yaml *.txt *.xlsx *.bat *zip *.dic *.toml *.csv *yml .env *.db .env.example tools tests *.ps1 *.json Rehab_RAG "PTガイドライン&Excel版書式(リハビリテーション総合実施計画書)" output nginx logs create .ruff_cache .pytest_cache .history __pycache__ *html 1_generate.py db_viewer.py debug_parser.py evaluate_extraction_accuracy.py rehab_db_viewer.py レイアウト.html style.css static -o context1.json
"""

import os
import sys
import json
import argparse
import subprocess
import fnmatch
import re
import ast
import math
import urllib.request
from collections import Counter
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
HAS_ONNX = False

try:
    import onnxruntime as ort
    from tokenizers import Tokenizer
    import numpy as np
    HAS_ONNX = True
except ImportError:
    pass

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
    ".ruff_cache", ".history", ".json", ".DS_Store", "package-lock.json", "yarn.lock", ".pytest_cache",
    ".onnx_cache"
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

    parser.add_argument('--summary-only', action='store_true', help='ファイルの中身の代わりに冒頭の要約コメントのみを出力する')
    parser.add_argument('--outline', action='store_true', help='ファイルの中身の代わりに関数やクラスのシグネチャ(アウトライン)を抽出して出力する')
    parser.add_argument('--smart-context', action='store_true', help='対象ファイルの依存先ファイルを自動検出し、アウトライン形式でコンテキストに追加する')
    parser.add_argument('--interactive', '-i', action='store_true', help='対話モード: ヒットしたファイルの出力形式を個別に選択する')
    parser.add_argument('--search', '-s', default=None, help='自然言語クエリで要約やタグをBM25検索し、関連ファイルを出力する')
    parser.add_argument('--search-full', action='store_true', help='検索対象を「要約+タグ」だけでなく「ファイル全体（全文）」に拡張する')
    parser.add_argument('--semantic-search', action='store_true', help='ONNXによる意味検索（セマンティック検索）を有効化')
    parser.add_argument('--full', nargs='*', default=[], help='全体を要約出力にする場合でも、指定したファイル名を含む場合は詳細(全文)を出力する')
    parser.add_argument('--top-k', type=int, default=5, help='検索時に関連度の高い上位N件のみを抽出する（デフォルト: 5）')

    parser.add_argument('--tag', nargs='*', help='指定したタグを完全に含むファイルのみを厳密に抽出する')
    parser.add_argument('--vocab-file', default='README.md', help='プロジェクト全体の共通タグ（ドメイン用語集）を抽出するためのファイル')
    parser.add_argument('--dry-run', action='store_true', help='ファイルを出力せず、検索や抽出の結果（対象ファイル一覧とタグ）のみをターミナルに表示する')
    
    parser.add_argument('--copy', '-c', action='store_true', help='クリップボードにコピー (要pyperclip)')
    parser.add_argument('--model', default='gpt-4o', help='トークン計算モデル (要tiktoken)')
    parser.add_argument('--debug', action='store_true', help='デバッグログ')
    parser.add_argument('--use-gitignore', action='store_true', help='.gitignoreのパターンを除外リストに追加')

    parser.add_argument('--tree', action='store_true', help='視覚的なツリー形式で出力（ファイルの中身は省略されます）')

    parser.add_argument('--text', action='store_true', help='Markdown風のテキスト形式で出力（トークン節約）')

    return parser.parse_args()

def log_debug(msg: str, is_debug: bool):
    if is_debug:
        print(f"[DEBUG] {msg}", file=sys.stderr)

# ==========================================
# 0. Cache Management
# ==========================================
CACHE_FILE_NAME = ".context_cache.json"

def load_cache(root_path: Path, is_debug: bool) -> Dict:
    cache_path = root_path / CACHE_FILE_NAME
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                log_debug(f"Loaded cache from {cache_path}", is_debug)
                return json.load(f)
        except Exception as e:
            log_debug(f"Failed to load cache: {e}", is_debug)
    return {}

def save_cache(root_path: Path, cache_data: Dict, is_debug: bool):
    cache_path = root_path / CACHE_FILE_NAME
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        log_debug(f"Saved cache to {cache_path}", is_debug)
    except Exception as e:
        log_debug(f"Failed to save cache: {e}", is_debug)

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
# 3.5. Summary Extraction
# ==========================================
def extract_summary(content: str, ext: str, is_debug: bool = False) -> str:
    """ファイルの冒頭から要約（コメントブロックやdocstring）を抽出する"""
    log_debug(f"Attempting to extract summary for extension: {ext}", is_debug)
    content = content.lstrip()
    
    # Python docstring (""" または ''')
    if content.startswith('"""'):
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if match:
            log_debug("Found Python double-quote docstring summary.", is_debug)
            return match.group(1).strip()
    if content.startswith("'''"):
        match = re.search(r"'''(.*?)'''", content, re.DOTALL)
        if match:
            log_debug("Found Python single-quote docstring summary.", is_debug)
            return match.group(1).strip()

    # C-style / CSS multiline (/* ... */)
    if content.startswith('/*'):
        match = re.search(r'/\*(.*?)\*/', content, re.DOTALL)
        if match:
            log_debug("Found C-style multiline comment summary.", is_debug)
            return match.group(1).strip()

    # HTML multiline (<!-- ... -->)
    if content.startswith('<!--'):
        match = re.search(r'<!--(.*?)-->', content, re.DOTALL)
        if match:
            extracted_text = match.group(1).strip()
            # デバッグ用に抽出したテキストの先頭30文字を出力
            log_debug(f"Found HTML comment summary: {extracted_text[:30]}...", is_debug)
            return extracted_text
        else:
            log_debug("Failed to find closing '-->'.", is_debug)

    # 単一行コメントの連続ブロック (# または //)
    summary_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if summary_lines: 
                break # コメントブロックの途中で空行が来たら終了とみなす
            continue
        
        if stripped.startswith('#') or stripped.startswith('//'):
            # 先頭のコメント記号を消して格納
            text = re.sub(r'^(#|//+)\s*', '', stripped)
            summary_lines.append(text)
        else:
            if summary_lines:
                break
            # コメントでも空行でもない行（実際のコードなど）が来たら即終了
            break
            
    if summary_lines:
        log_debug(f"Found single-line comment block summary ({len(summary_lines)} lines).", is_debug)
        return "\n".join(summary_lines)
        
    log_debug("No summary block found at the beginning.", is_debug)
    return ""

# ==========================================
# 3.5.5. TF-IDF & Global Vocabulary Helpers
# ==========================================
def compute_idf(documents: List[str]) -> Dict[str, float]:
    """コーパス全体から各単語の希少性(IDF)を計算する"""
    doc_count = len(documents)
    df = Counter()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'it', 'this', 'that'}
    for doc in documents:
        if not doc: continue
        words = set([w.lower() for w in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', doc)])
        words = words - stop_words
        df.update(words)
    
    idf = {}
    for word, count in df.items():
        # ゼロ除算回避とスムージングを入れたIDF
        idf[word] = math.log(doc_count / (1 + count)) + 1.0
    return idf

def build_global_vocab(vocab_path: Path, is_debug: bool) -> Set[str]:
    """READMEなどからプロジェクト特有の重要語彙を抽出する"""
    if not vocab_path.exists():
        log_debug(f"Global vocab file not found: {vocab_path}", is_debug)
        return set()
    try:
        content = vocab_path.read_text(encoding='utf-8', errors='ignore')
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'it', 'this', 'that'}
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', content)]
        filtered = [w for w in words if w not in stop_words]
        # 出現頻度上位50件をドメイン用語（共通タグ）としてセット
        top_words = {w for w, c in Counter(filtered).most_common(50)}
        log_debug(f"Loaded global vocab from {vocab_path.name}: {len(top_words)} words", is_debug)
        return top_words
    except Exception as e:
        log_debug(f"Failed to read vocab file {vocab_path}: {e}", is_debug)
        return set()

# ==========================================
# 3.6. Tag Extraction (AST / Tree-sitter)
# ==========================================
def extract_tags(content: str, summary: str, ext: str, is_debug: bool = False, global_vocab: Set[str] = None, idf_dict: Dict[str, float] = None) -> List[str]:
    """コード構造と自然言語（要約）の両方からタグを抽出し、リストとして返す"""
    tags = set()
    global_vocab = global_vocab or set()
    idf_dict = idf_dict or {}
    
# 0. 自然言語(要約)からの軽量キーワード抽出 (TF-IDF + Global Vocab)
    if summary:
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'it', 'this', 'that'}
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', summary)]
        filtered_words = [w for w in words if w not in stop_words]
        
        word_counts = Counter(filtered_words)
        scored_words = []
        
        for word, count in word_counts.items():
            # TF (Term Frequency)
            tf = count / len(filtered_words) if filtered_words else 0
            # IDF (Inverse Document Frequency)
            idf = idf_dict.get(word, 1.0) # 未知の単語はデフォルト1.0
            score = tf * idf
            
            # README由来の共通語彙に含まれていればスコアを2倍にブースト
            if word in global_vocab:
                score *= 2.0
                
            scored_words.append((word, score))
        
        # TF-IDFスコアの高い上位3件を抽出
        scored_words.sort(key=lambda x: x[1], reverse=True)
        for word, _ in scored_words[:3]:
            tags.add(word)

    # 1. Tree-sitterによる抽出 (多言語対応)
    if HAS_TREESITTER:
        lang_name = TREESITTER_EXT_MAP.get(ext)
        if lang_name:
            try:
                parser = get_parser(lang_name)
                content_bytes = content.encode('utf-8')
                tree = parser.parse(content_bytes)
                
                # 定義とみなすキーワード
                DEF_KEYWORDS = {'function', 'method', 'class', 'struct', 'interface'}
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
                            tags.add(node_name)

                    for child in node.children:
                        visit(child)

                visit(tree.root_node)
                if tags:
                    log_debug(f"Extracted {len(tags)} tags via Tree-sitter.", is_debug)
                    return sorted(list(tags))
            except Exception as e:
                log_debug(f"Tree-sitter tag extraction failed: {e}", is_debug)

    # 2. Python ASTによる抽出 (フォールバック)
    if ext == '.py':
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    tags.add(node.name)
            if tags:
                log_debug(f"Extracted {len(tags)} tags via AST.", is_debug)
                return sorted(list(tags))
        except Exception as e:
            log_debug(f"AST tag extraction failed: {e}", is_debug)

    # 3. 簡易正規表現による抽出 (他言語用フォールバック)
    try:
        patterns = [
            r'\b(?:class|def|function|struct|interface)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        for pat in patterns:
            for match in re.finditer(pat, content):
                tags.add(match.group(1))
        if tags:
            log_debug(f"Extracted {len(tags)} tags via Regex.", is_debug)
    except Exception:
        pass

    return sorted(list(tags))

# ==========================================
# 3.6.5. Outline (Signature) Extraction
# ==========================================
def extract_outline(content: str, ext: str, is_debug: bool = False) -> str:
    """ファイルからクラスや関数のシグネチャを抽出し、アウトラインを作成する"""
    log_debug(f"Extracting outline for extension: {ext}", is_debug)
    outlines = []
    lines = content.splitlines()

    if ext == '.py':
        # Python: class, def, async def の行を抽出
        for line in lines:
            if re.match(r'^\s*(class|def|async\s+def)\s+', line):
                clean_line = line.rstrip()
                if clean_line.endswith(':'):
                    outlines.append(f"{clean_line} ...")
                else:
                    outlines.append(f"{clean_line}: ...")

    elif ext in ['.js', '.jsx', '.ts', '.tsx']:
        # JS/TS: class, function, interface, type, const arrow functions
        for line in lines:
            stripped = line.strip()
            if re.match(r'^(export\s+)?(default\s+)?(class|function|interface|type)\s+', stripped) or \
               re.match(r'^(export\s+)?const\s+\w+\s*=\s*(\(.*?\)|[^=\s]+)\s*=>', stripped):
                clean_line = line.rstrip()
                if '{' in clean_line:
                    outlines.append(f"{clean_line.split('{')[0].rstrip()} {{ ... }}")
                else:
                    outlines.append(f"{clean_line} ...")

    elif ext in ['.java', '.c', '.cpp', '.cs', '.rs', '.go', '.php']:
        # 他言語: クラスや関数っぽい定義行
        for line in lines:
            stripped = line.strip()
            # 簡略化した正規表現でシグネチャを検知
            if re.match(r'^((public|private|protected|internal|export|func|fn)\s+)?(static\s+)?(class|struct|interface|impl)\s+', stripped) or \
               re.match(r'^((public|private|protected|internal|export|func|fn)\s+)?(static\s+)?[a-zA-Z_]\w*(<.*?>)?\s+[a-zA-Z_]\w*\s*\(', stripped):
                if stripped.endswith(';'): continue # プロトタイプ宣言などはスキップ
                clean_line = line.rstrip()
                if '{' in clean_line:
                    outlines.append(f"{clean_line.split('{')[0].rstrip()} {{ ... }}")
                else:
                    outlines.append(f"{clean_line} ...")

    else:
        # その他の言語の場合はフォールバックとして要約を返す
        return extract_summary(content, ext, is_debug)

    if outlines:
        return "\n".join(outlines)
    else:
        return "(No clear outline found)"

# ==========================================
# 3.7. Lightweight BM25 Search Engine
# ==========================================
class SimpleBM25:
    """標準ライブラリのみで実装した軽量BM25検索エンジン"""
    def __init__(self, corpus: List[str], k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        
        self._initialize(corpus)

    def _tokenize(self, text: str) -> List[str]:
        # 日本語や記号も考慮し、英数字とひらがなカタカナ漢字の連続をトークン化する簡易実装
        text = text.lower()
        # 記号を除去し、空白で分割 (簡易的だが、タグ検索などには十分)
        words = re.findall(r'\w+', text)
        return words

    def _initialize(self, corpus: List[str]):
        nd = {}
        num_doc = 0
        for document in corpus:
            self.doc_len.append(len(document))
            num_doc += len(document)

            frequencies = Counter(self._tokenize(document))
            self.doc_freqs.append(frequencies)

            for word, freq in frequencies.items():
                if word not in nd:
                    nd[word] = 0
                nd[word] += 1

        self.avgdl = num_doc / self.corpus_size if self.corpus_size > 0 else 0

        # IDFの計算
        for word, freq in nd.items():
            # BM25+ の式を少しアレンジして負のスコアを防ぐ
            idf_score = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[word] = idf_score

    def get_scores(self, query: str) -> List[float]:
        score = [0.0] * self.corpus_size
        query_words = self._tokenize(query)
        for q_word in query_words:
            if q_word not in self.idf:
                continue
            for index, frequencies in enumerate(self.doc_freqs):
                if q_word in frequencies:
                    freq = frequencies[q_word]
                    numerator = self.idf[q_word] * freq * (self.k1 + 1)
                    denominator = freq + self.k1 * (1 - self.b + self.b * self.doc_len[index] / self.avgdl)
                    score[index] += numerator / denominator
        return score

# ==========================================
# 3.8. ONNX Semantic Search Engine
# ==========================================
class ONNXSemanticSearch:
    """ONNX Runtimeを用いたローカル・セマンティック検索"""
    # 非常に軽量でコード検索にも強い 'all-MiniLM-L6-v2' の量子化モデルを使用 (約22MB)
    MODEL_URL = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model_quantized.onnx"
    TOKENIZER_URL = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer.json"
    
    def __init__(self, cache_dir: Path, is_debug: bool):
        self.is_debug = is_debug
        self.model_path = cache_dir / "model_quantized.onnx"
        self.tokenizer_path = cache_dir / "tokenizer.json"
        self._ensure_models(cache_dir)
        
        log_debug("Loading ONNX model and Tokenizer...", self.is_debug)
        self.tokenizer = Tokenizer.from_file(str(self.tokenizer_path))
        self.tokenizer.enable_padding(direction='right', pad_id=0, pad_type_id=0, pad_token='[PAD]')
        self.tokenizer.enable_truncation(max_length=256) # ノートPCのメモリに優しく長さを制限
        
        # 警告を抑制しつつCPUで推論
        opts = ort.SessionOptions()
        opts.log_severity_level = 3
        self.session = ort.InferenceSession(str(self.model_path), sess_options=opts, providers=['CPUExecutionProvider'])

    def _ensure_models(self, cache_dir: Path):
        cache_dir.mkdir(parents=True, exist_ok=True)
        if not self.model_path.exists():
            log_debug("Downloading lightweight ONNX model (approx 22MB)...", self.is_debug)
            urllib.request.urlretrieve(self.MODEL_URL, self.model_path)
        if not self.tokenizer_path.exists():
            log_debug("Downloading Tokenizer...", self.is_debug)
            urllib.request.urlretrieve(self.TOKENIZER_URL, self.tokenizer_path)

    def encode(self, texts: List[str]) -> 'np.ndarray':
        encodings = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        
        # ONNXの入力構成を取得
        input_names = [i.name for i in self.session.get_inputs()]
        ort_inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
        if "token_type_ids" in input_names:
            ort_inputs["token_type_ids"] = np.array([e.type_ids for e in encodings], dtype=np.int64)
            
        outputs = self.session.run(None, ort_inputs)
        
        # Mean Pooling処理 (各トークンのベクトルを平均して文全体のベクトルを作成)
        token_embeddings = outputs[0]
        input_mask_expanded = np.broadcast_to(np.expand_dims(attention_mask, -1), token_embeddings.shape)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = np.clip(input_mask_expanded.sum(1), a_min=1e-9, a_max=None)
        
        return sum_embeddings / sum_mask

    def get_scores(self, query: str, corpus: List[str]) -> List[float]:
        if not corpus: return []
        log_debug("Calculating semantic similarity with ONNX...", self.is_debug)
        
        query_vec = self.encode([query])[0]
        corpus_vecs = self.encode(corpus)
        
        # コサイン類似度の計算
        scores = []
        q_norm = np.linalg.norm(query_vec)
        for vec in corpus_vecs:
            v_norm = np.linalg.norm(vec)
            if q_norm == 0 or v_norm == 0:
                scores.append(0.0)
            else:
                sim = np.dot(query_vec, vec) / (q_norm * v_norm)
                scores.append(float(sim))
        return scores

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
    
    # 対象がディレクトリではなく単一ファイルの場合の直接処理
    if root_path.is_file():
        log_debug(f"Direct file path provided: {root_path}", args.debug)
        if should_exclude(root_path.name, args.exclude):
            return []
        if git_allowed is not None and str(root_path.resolve()) not in git_allowed:
            return []
        ext = root_path.suffix.lower()
        if (ext in args.preview_exts) or args.include_non_preview:
            return [root_path]
        return []

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

def load_gitignore_patterns(root_path: Path) -> List[str]:
    """ .gitignoreを読み込み、fnmatch用のパターンリストを返す """
    patterns = []
    gitignore_path = root_path / '.gitignore'
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # fnmatchはパス区切り(/)を厳密に扱わないため、
                    # 先頭や末尾の/を除去して単純なパターンにする
                    clean_pattern = line.strip('/')
                    patterns.append(clean_pattern)
        except Exception:
            pass
    return patterns


def print_visual_tree(node, prefix="", is_last=True):
    """
    JSON構造を再帰的に走査して、視覚的なツリーを表示する。
    """
    connector = "└──" if is_last else "├──"


    name = node['name']
    # "children" キーを持っている＝ディレクトリとみなして / を付与
    if "children" in node:
        name += "/"
        
    print(f"{prefix}{connector}{name}")

    
    # 子要素を取得
    children = node.get("children", [])
    
    # 最後の要素かどうか判定しながら再帰
    new_prefix = prefix + ("    " if is_last else "│   ")
    for i, child in enumerate(children):
        print_visual_tree(child, new_prefix, i == len(children) - 1)

def interactive_selection(targets: Set[Path], smart_deps: Set[Path]) -> Dict[Path, str]:
    """対話モードで各ファイルの出力形式を選択する"""
    file_modes = {}
    if not targets:
        return file_modes

    print("\n" + "="*60)
    print(" 🛠️  Interactive Mode: Select output format for each file")
    print(" [f] Full text   : ファイル全体を出力")
    print(" [s] Summary     : 冒頭の要約とタグのみを出力")
    print(" [o] Outline     : クラスと関数のシグネチャのみを出力")
    print(" [x] Exclude     : 出力から除外する")
    print("="*60 + "\n")
    
    # 見やすくするためにパス名でソートして順番に表示
    for p in sorted(list(targets)):
        is_dep = " [Dependency]" if p in smart_deps else ""
        while True:
            # 入力を促す (Enterだけ押した場合はデフォルトの 'f' になる)
            # 依存先ファイル(Dependency)の場合はデフォルトを 'o' (Outline) にする
            default_ans = 'o' if p in smart_deps else 'f'
            ans = input(f"📄 {p.name}{is_dep} [f/s/o/x] (default: {default_ans}): ").strip().lower()
            if ans == '':
                ans = default_ans
            if ans == '':
                ans = 'f'
            if ans in ['f', 's', 'o', 'x']:
                file_modes[p] = ans
                break
            print("  ⚠️ Invalid input. Please press f, s, o, or x.")
    
    print("\n" + "="*60 + "\n")
    return file_modes

def main():
    args = parse_args()
    root_path = Path(args.path).resolve()

    # キャッシュファイルのロードをメイン関数のスコープに設定
    global cache_dict
    cache_dict = load_cache(root_path if root_path.is_dir() else root_path.parent, args.debug)
    
    # 自身のキャッシュファイルを除外リストに追加
    args.exclude.append(CACHE_FILE_NAME)

    if args.tree:
        # 1. プレビュー対象拡張子を空にする (＝中身を読み込むファイルをゼロにする)
        args.preview_exts = []
        
        # 2. プレビュー対象外のファイルもツリーに含める設定をONにする
        #    これにより、フィルタ(-e)で除外されていない全ファイルが「中身なし」として登録される
        args.include_non_preview = True
        
        # 3. Focusモード（中身検索）はTree表示と相性が悪いため無効化しておく
        #    (ファイル名検索として機能させるなら残しても良いが、誤解を避けるためOFF推奨)
        args.focus = None 

    if args.use_gitignore:
        git_patterns = load_gitignore_patterns(root_path)
        args.exclude.extend(git_patterns)
        log_debug(f"Loaded .gitignore patterns: {git_patterns}", args.debug)

    if args.exclude != DEFAULT_EXCLUDES:
        args.exclude = list(set(args.exclude + DEFAULT_EXCLUDES))
    
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
    final_targets = set(file_map.keys())
    
    # ファイル名によるスコープ絞り込み機能を追加
    focus_keyword = args.focus
    path_filter = None

    if args.focus:
        # "filename:keyword" の形式なら分割する
        if ":" in args.focus:
            parts = args.focus.split(":")
            # 単純な分割だと Windowsパス(C:\...)と競合する可能性がゼロではないが、
            # 引数指定の文脈ではほぼファイルフィルタとして機能する
            if len(parts) == 2 and parts[0] and parts[1]:
                path_filter = parts[0]    # 例: "app.py" や "src"
                focus_keyword = parts[1]  # 例: "main"

        # 絞り込みロジック
        focus_roots = []
        for p, c in file_map.items():
            # 1. パスフィルタがある場合、パスに含まれていなければスキップ
            if path_filter and (path_filter not in str(p).replace(os.sep, '/')):
                continue

            # 2. ファイル名自体にキーワードが含まれていれば無条件で追加
            if focus_keyword in p.name:
                focus_roots.append(p)
                continue

            # 3. 中身に含まれる場合、「実際に関数やクラスとして定義されているか」を厳格にチェック
            if focus_keyword in c:
                extracted = None
                if HAS_TREESITTER:
                    extracted = extract_code_block_treesitter(c, p.suffix.lower(), focus_keyword)
                if not extracted and p.suffix.lower() == '.py':
                    extracted = extract_code_block_ast(c, focus_keyword)
                if not extracted:
                    extracted = extract_code_block_braces(c, focus_keyword)
                
                # 単なるコメントや "if __name__ == '__main__':" などではなく、
                # ちゃんと関数・クラス定義として抽出できた場合のみターゲットとする
                if extracted:
                    focus_roots.append(p)

        if args.resolve_deps and HAS_NETWORKX:
            G = build_dependency_graph(file_map, args.debug)
            final_targets = get_related_files(focus_roots, G)
        else:
            final_targets = set(focus_roots)
            
        # extract処理用に引数を書き換えておく（抽出関数にはキーワードだけ渡すため）
        args.focus = focus_keyword

    # --- [NEW] Global Vocab & TF-IDF Setup ---
    global_vocab = build_global_vocab(root_path / args.vocab_file, args.debug)
    
    log_debug("Computing IDF for TF-IDF tagging...", args.debug)
    all_summaries = []
    for p in final_targets:
        c = file_map.get(p, "")
        if c:
            all_summaries.append(extract_summary(c, p.suffix.lower(), False))
    idf_dict = compute_idf(all_summaries)

    # 対象ファイルのタグを前もって生成・保持 (タグ検索とDry-run用)
    file_tags_map = {}
    for item in list(final_targets):
        content = file_map.get(item, "")
        summary_text = extract_summary(content, item.suffix.lower(), False)
        tags = extract_tags(content, summary_text, item.suffix.lower(), args.debug, global_vocab, idf_dict)
        file_tags_map[item] = tags

    # --- [NEW] Strict Tag Filtering ---
    if args.tag:
        log_debug(f"Filtering by strict tags: {args.tag}", args.debug)
        required_tags = {t.lower() for t in args.tag}
        filtered_targets = set()
        for item in final_targets:
            item_tags = {t.lower() for t in file_tags_map.get(item, [])}
            # 指定された全タグを含んでいる場合のみ通過
            if required_tags.issubset(item_tags):
                filtered_targets.add(item)
        final_targets = filtered_targets
        if not final_targets:
            print(">> 指定されたタグを持つファイルは見つかりませんでした。", file=sys.stderr)

    # --- [NEW] Dry-Run Mode ---
    if args.dry_run:
        print("\n" + "="*60)
        print(" 🔍 DRY RUN / SEARCH PREVIEW")
        print("="*60)
        if not final_targets:
            print(" No matching files found.")
        else:
            for item in sorted(final_targets):
                tags_str = ", ".join(file_tags_map.get(item, []))
                print(f"📄 {item.relative_to(root_path)} \n   └─ [Tags: {tags_str}]\n")
        print("="*60 + "\n")
        sys.exit(0)

    # --- BM25 Search Logic ---
    if args.search and final_targets:
        log_debug(f"Starting BM25 search for query: '{args.search}'", args.debug)
        
        # 1. 検索対象のドキュメント（要約＋タグ）を準備
        search_corpus = []
        target_list = list(final_targets) # インデックスと同期させるためリスト化
        
        # 検索には必ず要約とタグが必要なため、一度キャッシュから引っ張るかパースする
        # (ここでパースしたものはキャッシュに乗るため、後続のツリー構築ではHITする)
        for item in target_list:
            content = file_map[item]
            item_str = str(item.resolve())
            try:
                current_mtime = os.path.getmtime(item)
            except Exception:
                current_mtime = 0
            
            # キャッシュから要約コンテンツを取得
            cached_content = ""
            if item_str in cache_dict and cache_dict[item_str].get("mtime") == current_mtime:
                cached_content = cache_dict[item_str].get("cached_content", "")
            else:
                summary_text = extract_summary(content, item.suffix.lower(), False)
                # 変更: vocabとidf辞書を渡してTF-IDF抽出を行う
                tags = extract_tags(content, summary_text, item.suffix.lower(), False, global_vocab, idf_dict)
                if tags:
                    tag_str = ", ".join(tags)
                    cached_content = f"{summary_text}\n\n[Tags: {tag_str}]"
                else:
                    cached_content = summary_text
                
                # ここでひっそりキャッシュを更新しておく
                cache_dict[item_str] = {
                    "mtime": current_mtime,
                    "cached_content": cached_content
                }
            
            # 変更: 全文検索フラグがONの場合は、ファイル本文もコーパスに結合する
            if getattr(args, 'search_full', False):
                search_corpus.append(f"{cached_content}\n\n{content}")
            else:
                search_corpus.append(cached_content)

        # 2. 検索エンジンの初期化とスコアリング
        if search_corpus:
            bm25_scores = [0.0] * len(search_corpus)
            onnx_scores = [0.0] * len(search_corpus)

            # BM25スコアリング (キーワード一致)
            bm25 = SimpleBM25(search_corpus)
            bm25_scores = bm25.get_scores(args.search)

            # ONNXスコアリング (意味の一致)
            if getattr(args, 'semantic_search', False) and HAS_ONNX:
                onnx_cache_dir = root_path / ".onnx_cache"
                onnx_engine = ONNXSemanticSearch(onnx_cache_dir, args.debug)
                onnx_scores = onnx_engine.get_scores(args.search, search_corpus)
            elif getattr(args, 'semantic_search', False) and not HAS_ONNX:
                log_debug("ONNX runtime dependencies are missing. Install with: pip install onnxruntime tokenizers numpy", args.debug)

            # 3. ハイブリッド・スコアリング (正規化と結合)
            # BM25スコアを 0.0 ~ 1.0 に正規化
            max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
            norm_bm25 = [s / max_bm25 for s in bm25_scores]
            
            # ONNXスコアの負の値を丸める
            norm_onnx = [max(0.0, s) for s in onnx_scores]

            # セマンティック検索有効時は ONNXを7割、BM25を3割の重みでハイブリッド
            if getattr(args, 'semantic_search', False) and HAS_ONNX:
                combined_scores = [(0.3 * b) + (0.7 * o) for b, o in zip(norm_bm25, norm_onnx)]
            else:
                combined_scores = norm_bm25

            # スコア付きでソート
            scored_results = sorted(zip(target_list, combined_scores, bm25_scores, onnx_scores), key=lambda x: x[1], reverse=True)
            
            search_hits = set()
            hit_count = 0
            for file_path, c_score, b_score, o_score in scored_results:
                # 複合スコアが一定以上(0.1以上)の有意な結果のみ対象とし、上位 top_k 件で打ち切る
                if c_score >= 0.1:
                    log_debug(f"Search HIT [Rank {hit_count+1}] [Combined: {c_score:.3f} | BM25: {b_score:.3f}, ONNX: {o_score:.3f}] - {file_path.name}", args.debug)
                    search_hits.add(file_path)
                    hit_count += 1
                    
                    if hit_count >= args.top_k:
                        break
            
            if search_hits:
                # 絞り込み結果でターゲットを上書き
                final_targets = search_hits
                
                # 検索モードの場合は、強制的に summary_only を ON にして結果を見やすくする
                args.summary_only = True 
            else:
                log_debug("No related files found for the query.", args.debug)
                final_targets = set() # ヒットしなかった場合は空にする

    # --- Smart Context Logic ---
    smart_deps = set()
    if getattr(args, 'smart_context', False) and HAS_NETWORKX and final_targets:
        log_debug("Resolving smart context (dependencies)...", args.debug)
        G = build_dependency_graph(file_map, args.debug)
        if G:
            for p in list(final_targets):
                if p in G:
                    # 直接の依存先（importされているファイル）を取得
                    for dep in G.successors(p):
                        if dep not in final_targets:
                            smart_deps.add(dep)
            if smart_deps:
                log_debug(f"Found {len(smart_deps)} dependency files for smart context.", args.debug)
                final_targets.update(smart_deps)

    # --- Interactive Mode Logic ---
    file_output_modes = {}
    if args.interactive and final_targets:
        file_output_modes = interactive_selection(final_targets, smart_deps)
        # 'x' (除外) が選ばれたファイルをターゲットから削除する
        final_targets = {p for p in final_targets if file_output_modes.get(p) != 'x'}
        smart_deps = {p for p in smart_deps if file_output_modes.get(p) != 'x'}

    # Build Tree
    def build_tree(current_path):
        # 共通処理: ファイルノードの生成
        def _create_file_node(item: Path):
            content = file_map[item]
            is_smart_dep = item in smart_deps
            
            # アウトラインモード、またはSmart Contextによる依存先ファイルの場合はシグネチャを抽出して上書き
            if (getattr(args, 'outline', False) or is_smart_dep) and content:
                outline_text = extract_outline(content, item.suffix.lower(), args.debug)
                if is_smart_dep:
                    content = f"// [Smart Context: Auto-resolved Dependency Outline]\n{outline_text}"
                else:
                    content = outline_text
                
            # 要約のみモードの場合は、中身をパースして上書き
            elif getattr(args, 'summary_only', False) and content:
                # 追加: --full で指定されたファイル名が含まれていれば要約化をスキップ（全文のままにする）
                is_forced_full = any(f in item.name for f in getattr(args, 'full', []))
                
                if not is_forced_full:
                    item_str = str(item.resolve())
                    try:
                        current_mtime = os.path.getmtime(item)
                    except Exception:
                        current_mtime = 0
                    
                    # キャッシュヒットチェック
                    if item_str in cache_dict and cache_dict[item_str].get("mtime") == current_mtime:
                        log_debug(f"Cache HIT for: {item.name}", args.debug)
                        content = cache_dict[item_str].get("cached_content", "")
                    else:
                        log_debug(f"Cache MISS (or updated) for: {item.name}. Parsing...", args.debug)
                        
                        # 1. 要約の抽出
                        summary_text = extract_summary(content, item.suffix.lower(), args.debug)
                        if not summary_text:
                            summary_text = "(No summary provided)"
                        
                        # 2. 構造タグと自然言語タグの両方を抽出 (引数変更)
                        tags = extract_tags(content, summary_text, item.suffix.lower(), args.debug, global_vocab, idf_dict)
                    
                    # 3. コンテキストの結合
                    if tags:
                        tag_str = ", ".join(tags)
                        content = f"{summary_text}\n\n[Tags: {tag_str}]"
                    else:
                        content = summary_text
                        
                    # キャッシュの更新
                    cache_dict[item_str] = {
                        "mtime": current_mtime,
                        "cached_content": content
                    }
                    
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
            return {"name": item.name, "preview": preview_text}

        # 1. パスが単一ファイルの場合の直接処理
        if current_path.is_file():
            if current_path in final_targets:
                return _create_file_node(current_path)
            return None

        # 2. パスがディレクトリの場合の再帰処理
        node = {"name": current_path.name}
        if current_path.is_dir():
            children = []
            try:
                for item in sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if should_exclude(item.name, args.exclude):
                        continue
                    
                    if item.is_dir():
                        child = build_tree(item)
                        # 子ディレクトリを追加する条件を緩和
                        if child:
                            if args.directories_only:
                                children.append(child)
                            elif child.get("children") or child.get("files_inside"):
                                children.append(child)
                                
                    elif item in final_targets:
                        children.append(_create_file_node(item))

            except Exception:
                pass
            
            node["children"] = children
            node["files_inside"] = len(children) > 0
            
            # 自身を返す条件を緩和
            if args.directories_only:
                return node
            
            return node if node["files_inside"] else None
        
        return None


    root_node = build_tree(root_path)
    
    # Output
    if root_node:
        try:

            if args.tree:
                
                # ルートディレクトリ名を表示 (ディレクトリらしさを出すため / を付与)
                print(f"{root_node['name']}/")
                
                # ルート直下の子要素に対して再帰表示を実行
                children = root_node.get("children", [])
                for i, child in enumerate(children):
                    is_last = (i == len(children) - 1)
                    print_visual_tree(child, prefix="", is_last=is_last)
                
                return # ツリー表示だけして終了
            
            if args.text:
                log_debug("Generating Markdown text output...", args.debug)
                def generate_text_from_tree(node, current_path=""):
                    text_parts = []
                    # ディレクトリの場合
                    if "children" in node:
                        for child in node["children"]:
                            # 親パスと子要素の名前を結合して現在のパスを生成
                            child_path = f"{current_path}/{child['name']}".strip('/') if current_path else child['name']
                            text_parts.extend(generate_text_from_tree(child, child_path))
                    # ファイル単体の場合
                    else:
                        file_path = current_path if current_path else node['name']
                        if node.get("preview") is not None and node.get("preview") != "":
                            ext = '.' + node['name'].split('.')[-1].lower() if '.' in node['name'] else ''
                            lang = TREESITTER_EXT_MAP.get(ext, "")
                            text_parts.append(f"### File: {file_path}\n```{lang}\n{node['preview']}\n```\n")
                            log_debug(f"Added content for text output: {file_path}", args.debug)
                        else:
                            text_parts.append(f"### File: {file_path} (No content preview)\n")
                            log_debug(f"Added file path only for text output: {file_path}", args.debug)
                    return text_parts

                text_lines = generate_text_from_tree(root_node)
                output_str = "\n".join(text_lines)
            else:
                log_debug("Generating JSON output...", args.debug)
                output_str = json.dumps(root_node, ensure_ascii=False, indent=None, separators=(',', ':'))
            
            # Token Count
            count = len(output_str) // 4
            if HAS_TIKTOKEN:
                try:
                    count = len(tiktoken.encoding_for_model(args.model).encode(output_str))
                    log_debug("Token count calculated via tiktoken.", args.debug)
                except Exception as e:
                    log_debug(f"Tiktoken encoding failed: {e}. Falling back to heuristic calculation.", args.debug)
                    pass
            print(f"[Tokens: {count:,}]", file=sys.stderr)

            if args.outfile:
                with open(args.outfile, 'w', encoding='utf-8') as f:
                    f.write(output_str)
                print(f"Saved to {args.outfile}")
                
            # キャッシュの保存 (キャッシュの中身が更新されている可能性があるため常に保存を試みる)
            if cache_dict:
                save_cache(root_path if root_path.is_dir() else root_path.parent, cache_dict, args.debug)
            
            # コピー指定がある場合の処理
            elif args.copy:
                if HAS_PYPERCLIP:
                    pyperclip.copy(output_str)
                    print(">> Copied to clipboard! <<", file=sys.stderr)
                else:
                    print(">> [ERROR] クリップボードへのコピーに失敗しました。", file=sys.stderr)
                    print(">> 必要なライブラリが見つかりません: pip install pyperclip", file=sys.stderr)
                    print(">> 代わりに標準出力に表示します:\n", file=sys.stderr)
                    print(output_str)

            # ファイル指定もコピー指定もない場合（標準出力）
            else:
                print(output_str)

        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
    else:
        print("No files matched.", file=sys.stderr)

if __name__ == "__main__":
    main()