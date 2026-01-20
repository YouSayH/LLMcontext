import argparse
import install_deps
import create_tree
import write_code

def main():
    parser = argparse.ArgumentParser(description='LLMの出力からプロジェクトを構築します')
    parser.add_argument('text', help='LLMの出力テキスト（ツリー図やコードを含む文字列）')
    
    # 実行モードのフラグ
    parser.add_argument('--pip', action='store_true', help='pip installのみ実行')
    parser.add_argument('--tree', action='store_true', help='ディレクトリ作成のみ実行')
    parser.add_argument('--code', action='store_true', help='コード書き込みのみ実行')
    
    args = parser.parse_args()
    text = args.text

    # 引数が何も指定されていない場合は全て実行
    run_all = not (args.pip or args.tree or args.code)

    if run_all or args.pip:
        install_deps.install(text)

    if run_all or args.tree:
        create_tree.create(text)

    if run_all or args.code:
        write_code.write(text)

    print("\n全工程が完了しました。")

if __name__ == "__main__":
    main()