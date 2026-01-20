### 実行方法

すべてのファイルを同じフォルダに置き、コマンドプロンプトやPowerShellで実行します。

#### 1. 全てを一括実行する場合

（デフォルトの動作です）

```powershell
python main.py @'
(ここにLLMの出力をペースト)
'@

```

#### 2. ディレクトリ作成だけ試したい場合

```powershell
python main.py --tree @'
(ここにLLMの出力をペースト)
'@

```

または、単体スクリプトを直接呼ぶことも可能です。

```powershell
python create_tree.py @'
(ここにLLMの出力をペースト)
'@

```

#### 3. コードの書き込みだけやり直したい場合

（手動でフォルダを作った後や、コード生成だけリトライしたい時）

```powershell
python main.py --code @'
(ここにLLMの出力をペースト)
'@

```
