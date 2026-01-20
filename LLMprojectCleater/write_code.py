import os
import sys
import re

def write(text):
    print("\n--- [3] コードの書き込み ---")
    
    # 1. ルートディレクトリ名の特定（ツリー図から推測）
    # server.pyなどを正しいフォルダに入れるためにルートが必要
    root_match = re.search(r'([\w_-]+)/\s*\n├──', text)
    root_dir = root_match.group(1) if root_match else "."
    
    lines = text.split('\n')
    current_file = None
    code_block_active = False
    code_content = []
    
    # ファイル名を特定する正規表現
    # パターン例: "### 3. 実装 (server.py)" や "### server.py"
    file_pattern = re.compile(r'###.*?[\(`]([\w\-\./]+\.[a-zA-Z0-9]+)[\)`]?')

    for line in lines:
        # ヘッダー行からファイル名を検出
        if "###" in line:
            match = file_pattern.search(line)
            if match:
                current_file = match.group(1)
                # ルートディレクトリを含まないパスの場合、ルートを付与
                if root_dir != "." and not current_file.startswith(root_dir):
                    current_file = os.path.join(root_dir, current_file)
                print(f"ターゲット検出: {current_file}")
                continue

        # コードブロックの検出
        if line.strip().startswith("```"):
            if code_block_active:
                # ブロック終了 -> 書き込み実行
                if current_file:
                    # 親フォルダがない場合は作成（念のため）
                    os.makedirs(os.path.dirname(current_file), exist_ok=True)
                    
                    with open(current_file, 'w', encoding='utf-8') as f:
                        f.write("\n".join(code_content))
                    print(f"[WRITE] {current_file} に書き込みました")
                    
                    current_file = None
                    code_content = []
                code_block_active = False
            else:
                # ブロック開始
                code_block_active = True
                code_content = []
            continue
        
        if code_block_active and current_file:
            code_content.append(line)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        write(sys.argv[1])