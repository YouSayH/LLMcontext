import json
import glob
import os
from excel_mapper import analyze_excel_for_llm

class ExcelAgentToolkit:
    """
    LLMがExcelを操作するためのツールセット。
    excel_mapper.py の視覚化機能を利用して、構造を把握します。
    """

    def get_excel_structure(self, file_path: str = None, sheet_name: str = None) -> str:
        """
        【ツール定義】
        Excelファイルの構造（入力欄の位置、結合セル、既存の値）を地図として取得します。
        書き込みを行う前に必ずこのツールを実行して、正しい座標 {__INPUT_HERE__} を確認してください。
        
        Args:
            file_path (str, optional): 対象のExcelファイルパス。指定がない場合はカレントディレクトリの全Excelファイルをスキャンします。
            sheet_name (str, optional): シート名。指定がない場合は全シートを読み込みます。
        
        Returns:
            str: Excelシートの構造を表すテキストデータ
        """
        # ファイル指定がない場合：カレントディレクトリの全xlsxファイルを対象にする
        if not file_path:
            xlsx_files = glob.glob("*.xlsx")
            if not xlsx_files:
                return "No .xlsx files found in the current directory."
            
            results = []
            results.append(f"Found {len(xlsx_files)} Excel files. Scanning all...\n")
            for f in xlsx_files:
                # excel_mapperの関数を呼び出し
                file_result = analyze_excel_for_llm(f, sheet_name)
                results.append(f"FILE: {f}\n{file_result}")
            
            return "\n\n".join(results)

        # ファイル指定がある場合
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' not found."
            
        return analyze_excel_for_llm(file_path, sheet_name)

    def get_tool_definition(self):
        """
        LLM (OpenAI APIなど) に渡すための Function Calling 用の定義JSONを返します。
        """
        return {
            "type": "function",
            "function": {
                "name": "get_excel_structure",
                "description": "Excelファイルの構造マップ（入力すべき欄 {__INPUT_HERE__} の座標、結合セル、値）を取得する。ファイル名を省略するとフォルダ内の全Excelファイルをスキャンする。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "読み込むExcelファイルのパス (例: 'data.xlsx')。省略時は全ファイルを読み込む。",
                            "nullable": True
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "特定のシートのみ読み込む場合のシート名",
                            "nullable": True
                        }
                    },
                    # file_path を必須から外しました（省略可能に）
                    "required": [] 
                }
            }
        }

# --- 動作確認用 ---
if __name__ == "__main__":
    import argparse
    
    # 引数の設定
    parser = argparse.ArgumentParser(description="Test ExcelAgentToolkit")
    parser.add_argument("filename", nargs="?", help="Target Excel filename")
    parser.add_argument("sheetname", nargs="?", help="Target Sheet name")
    args = parser.parse_args()

    toolkit = ExcelAgentToolkit()

    # 引数がある場合：その指示通りに実行して終了
    if args.filename:
        # シート名が None の場合も get_excel_structure は対応済み
        print(toolkit.get_excel_structure(args.filename, args.sheetname))

    # 引数がない場合：デモモード（JSON定義の表示 ＋ 全ファイルスキャン）
    else:
        print("--- 1. Tool Definition (JSON) ---")
        print(json.dumps(toolkit.get_tool_definition(), indent=2, ensure_ascii=False))
        
        print("\n--- 2. Execution Test (Scan All) ---")
        # 引数なしで実行 -> 全ファイルスキャン
        print(toolkit.get_excel_structure())