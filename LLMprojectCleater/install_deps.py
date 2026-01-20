import sys
import re
import subprocess

def install(text):
    print("\n--- [1] 依存ライブラリのインストール ---")
    # pip install コマンドの抽出
    matches = re.findall(r'pip install ([\w\s-]+)', text)
    
    if not matches:
        print("インストールコマンドが見つかりませんでした。スキップします。")
        return

    for packages in matches:
        packages = packages.strip()
        print(f"実行中: pip install {packages}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages.split())
            print("インストール成功")
        except subprocess.CalledProcessError as e:
            print(f"エラー: インストールに失敗しました - {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        install(sys.argv[1])