import os
import sys
import re

def create(text):
    print("\n--- [2] ディレクトリ構成の作成 ---")
    
    # 1. コードブロック (```...```) をすべて抽出する
    #    解説文をフォルダ名として誤検知しないためのガード処理です
    blocks = re.findall(r'```[\w]*\n(.*?)```', text, re.DOTALL)
    
    target_lines = []
    found_tree_block = False

    # 2. ツリー構造（├── や └──）が含まれるブロックを探す
    for block in blocks:
        if '├──' in block or '└──' in block:
            target_lines = block.splitlines()
            found_tree_block = True
            break
            
    # ブロックが見つからなかった場合のフォールバック（念のため全体から探す）
    if not found_tree_block:
        target_lines = text.splitlines()

    stack = [] # (indent_level, full_path)

    for line in target_lines:
        # コメント(#以降)と右空白の削除
        content = line.split('#')[0].rstrip()
        if not content.strip():
            continue

        # ガード処理: 日本語が含まれる行や、長すぎる行はパスではないとみなしてスキップ
        # これにより、ブロック抽出に失敗しても解説文によるエラーを防ぎます
        if re.search(r'[ぁ-んァ-ン一-龥]', content) or len(content) > 100:
            continue

        # ツリー解析
        match = re.match(r'^([│├─└\s]*)(.*)', content)
        if not match:
            continue
            
        prefix = match.group(1)
        name = match.group(2).strip()
        
        if not name:
            continue
            
        # ガード処理2: インデントがなく、拡張子もなく、スラッシュでも終わらないものは無視
        # (ただし Makefile や Dockerfile などの例外はありえるが今回は無視)
        if len(prefix) == 0 and not (name.endswith('/') or '.' in name):
            continue

        current_indent = len(prefix)

        # 親ディレクトリの調整
        while stack and stack[-1][0] >= current_indent:
            stack.pop()
        
        parent_path = stack[-1][1] if stack else "."
        current_path = os.path.join(parent_path, name)
        
        # ディレクトリかファイルの判定
        is_dir = name.endswith('/') or ('.' not in os.path.basename(name))
        
        try:
            if is_dir:
                if not os.path.exists(current_path):
                    os.makedirs(current_path)
                    print(f"[MKDIR] {current_path}")
                # スタックに追加
                stack.append((current_indent, current_path))
            else:
                # ファイル作成
                parent_dir = os.path.dirname(current_path)
                if parent_dir and parent_dir != "." and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                    
                if not os.path.exists(current_path):
                    with open(current_path, 'w', encoding='utf-8') as f:
                        pass 
                    print(f"[TOUCH] {current_path}")
                else:
                    print(f"[EXIST] {current_path}")
                    
        except OSError as e:
            # 万が一無効な文字があっても停止せずにスキップする
            print(f"[SKIP] 無効なパスのためスキップ: {name} ({e})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create(sys.argv[1])