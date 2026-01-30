"""
# ipynb_context.py - Jupyter Notebook Context Extractor for LLMs

Jupyter Notebook (.ipynb) の内容を、LLM（ChatGPT, Gemini, Claude等）に
共有・相談するために最適化してテキスト出力するCLIツールです。

## 特徴
- **トークン節約**: 画像(base64)を除外し、テキスト/コード/エラーのみを抽出。
- **整形出力**: LLMが理解しやすいMarkdown形式（```python ...）で出力。
- **柔軟なフィルタ**: コードのみ、エラーのみ、出力のみなど、状況に応じて構成可能。
- **コメント除去**: コード内のコメントアウトを削除し、さらにトークンを削減可能。
- **Windows対応**: リダイレクト時(> out.txt)の文字化けを自動防止。

## 基本的な使い方
ターミナルで以下のように実行します。
$ python ipynb_context.py [ファイルパス] [オプション]

## ユースケース別コマンド例

1. 【デフォルト】全ての内容を共有（学習用教材など）
   Markdown、コード、実行結果の全てを出力します。
   $ python ipynb_context.py notebook.ipynb

2. 【ロジック相談】コードのみを共有（Markdownや結果は不要）
   純粋なロジックを見せてリファクタリングを依頼する場合などに。
   $ python ipynb_context.py notebook.ipynb --no-markdown --no-output

3. 【デバッグ依頼】エラーが出たセルのみ抽出
   エラーが発生したコードとスタックトレースのみを抜き出します。
   $ python ipynb_context.py notebook.ipynb --only-error

4. 【トークン削減】コメントを除外してコード共有
   `#` で始まるコメント行やインラインコメントを削除して出力します。
   $ python ipynb_context.py notebook.ipynb --no-markdown --no-output --no-comments

5. 【作業の続き】直近の実行結果 n件のみ共有
   過去の履歴は不要で、直近の作業内容だけを共有したい場合に。
   $ python ipynb_context.py notebook.ipynb -n 5

6. 【ログ抽出】実行結果のみを取得
   コードや説明は不要で、ログやprint出力だけを見たい場合に。
   $ python ipynb_context.py notebook.ipynb --no-code --no-markdown

## オプション一覧
  -h, --help       ヘルプを表示
  -n, --tail N     最後の N 件のセルのみ出力
  --json           JSON形式で出力（API連携用）
  --no-markdown    Markdownセルを除外
  --no-code        ソースコードを除外（出力結果のみ欲しい場合）
  --no-output      実行結果を除外（コードのみ欲しい場合）
  --no-comments    コード内のコメント(#)を削除
  --only-error     エラーが発生しているセルのみ抽出
"""


import json
import argparse
import sys
import re
from typing import List, Dict, Any, Optional

def load_notebook(file_path: str) -> Dict[str, Any]:
    """Notebookファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file: {file_path}", file=sys.stderr)
        sys.exit(1)

def remove_comments(source: str) -> str:
    """文字列リテラルを保護しつつ、コメント(#以降)を削除する"""
    # 正規表現: 文字列リテラル(グループ1) または コメント(グループ2) にマッチ
    pattern = r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(#.*)'
    
    def replace(match):
        if match.group(1):  # 文字列リテラルの場合はそのまま維持
            return match.group(1)
        else:  # コメントの場合は削除
            return ""

    lines = source.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # 行ごとにコメント削除を実行
        cleaned = re.sub(pattern, replace, line)
        # コメント削除後に空行(空白のみ)になった場合は除外
        if cleaned.strip():
            cleaned_lines.append(cleaned.rstrip()) # 行末の空白も除去
            
    return "\n".join(cleaned_lines)

def format_output_text(cell_type: str, source: str, outputs: str = "") -> str:
    """LLMが認識しやすいテキスト形式に整形する"""
    formatted = ""
    
    if cell_type == 'markdown':
        formatted += f"### Markdown:\n{source}\n"
    elif cell_type == 'code':
        # ソースがある場合のみコードブロックを表示
        if source.strip():
            formatted += f"### Code:\n```python\n{source}\n```\n"
        
        # 出力がある場合のみ出力ブロックを表示
        if outputs:
            formatted += f"### Output:\n```text\n{outputs}\n```\n"
            
    return formatted + "\n"

def extract_traceback(outputs: List[Dict[str, Any]]) -> str:
    """エラー出力からTracebackを抽出する"""
    error_text = []
    for output in outputs:
        if output.get('output_type') == 'error':
            # tracebackはリスト形式で格納されている
            trace = output.get('traceback', [])
            error_text.append("\n".join(trace))
    return "\n".join(error_text)

def extract_std_output(outputs: List[Dict[str, Any]]) -> str:
    """標準出力や実行結果テキストを抽出する（画像などは除外）"""
    text_outputs = []
    for output in outputs:
        # stream (print文など)
        if output.get('output_type') == 'stream':
            text = output.get('text', [])
            if isinstance(text, list):
                text_outputs.append("".join(text))
            else:
                text_outputs.append(text)
        # execute_result (変数の表示など)
        elif output.get('output_type') == 'execute_result':
            data = output.get('data', {})
            if 'text/plain' in data:
                text = data['text/plain']
                if isinstance(text, list):
                    text_outputs.append("".join(text))
                else:
                    text_outputs.append(text)
        # error
        elif output.get('output_type') == 'error':
            text_outputs.append(extract_traceback([output]))
            
    return "\n".join(text_outputs)

def process_notebook(
    notebook: Dict[str, Any], 
    limit: Optional[int] = None,
    no_comments: bool = False,
    no_markdown: bool = False,
    no_code: bool = False,
    no_output: bool = False,
    only_error: bool = False
) -> List[Dict[str, Any]]:
    """フラグに基づいてセルをフィルタリング・加工する"""
    
    cells = notebook.get('cells', [])
    processed_cells = []

    for cell in cells:
        cell_type = cell.get('cell_type')
        source_raw = cell.get('source', [])
        source = "".join(source_raw) if isinstance(source_raw, list) else source_raw
        
        # --- フィルタリング 1: Markdownの除外 ---
        if no_markdown and cell_type == 'markdown':
            continue
        
        # [修正点] no_codeの場合でも、実行結果を取得するためにここではcontinueしない

        # --- 加工: コメント除去 ---
        if no_comments and cell_type == 'code':
            source = remove_comments(source)

        # 空のセルはスキップ
        if not source.strip():
            continue

        # --- 出力の取得 ---
        outputs_raw = cell.get('outputs', [])
        has_error = any(o.get('output_type') == 'error' for o in outputs_raw)
        
        # Outputを含めるかどうか
        if no_output or cell_type != 'code':
            outputs_text = ""
        else:
            outputs_text = extract_std_output(outputs_raw)

        # --- フィルタリング 2: エラー有無による除外 ---
        if only_error:
            if not has_error:
                continue

        # [修正点] no_codeが指定されている場合、sourceを空にする（Outputだけ残すため）
        display_source = source
        if no_code and cell_type == 'code':
            display_source = ""

        item = {
            "type": cell_type,
            "source": display_source,
            "output": outputs_text,
            "has_error": has_error
        }

        processed_cells.append(item)

    # 最新n件の処理
    if limit is not None and limit > 0:
        processed_cells = processed_cells[-limit:]

    return processed_cells

def main():
    # Windowsでのファイルリダイレクト時の文字化け防止 (強制的にUTF-8出力)
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Convert .ipynb content for LLM context sharing.")
    
    parser.add_argument("file", help="Path to the .ipynb file")
    
    # --- 表示コンポーネントの制御 ---
    parser.add_argument("--no-markdown", action="store_true", help="Exclude markdown cells.")
    parser.add_argument("--no-code", action="store_true", help="Exclude code source (output only).")
    parser.add_argument("--no-output", action="store_true", help="Exclude execution outputs.")

    # --- フィルタリング ---
    parser.add_argument("--only-error", action="store_true", help="Show only cells that have errors.")
    
    # 件数指定（最新n件）
    parser.add_argument(
        "-n", "--tail", 
        type=int, 
        help="Output only the last N processed cells."
    )

    # コメント除外オプション
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Remove comment lines starting with '#' from code cells."
    )
    
    # 出力フォーマット
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output result as JSON format instead of formatted text."
    )

    args = parser.parse_args()

    notebook = load_notebook(args.file)
    
    # 処理実行
    result_cells = process_notebook(
        notebook, 
        limit=args.tail, 
        no_comments=args.no_comments,
        no_markdown=args.no_markdown,
        no_code=args.no_code,
        no_output=args.no_output,
        only_error=args.only_error
    )

    # 出力
    if args.json:
        # JSON形式で出力（プログラム連携用）
        print(json.dumps(result_cells, ensure_ascii=False, indent=2))
    else:
        # テキスト形式で出力（LLMプロンプト貼り付け用）
        if not result_cells:
            print("(No relevant cells found matching the criteria)")
        
        for cell in result_cells:
            text = format_output_text(cell['type'], cell['source'], cell['output'])
            # 空行のみの結果になるのを防ぐ
            if text.strip():
                print(text)
                print("-" * 40) # セパレータ

if __name__ == "__main__":
    main()