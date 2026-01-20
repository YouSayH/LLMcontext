# Show-Tree.ps1 人間用(CLI上のビジュアル重視)


param(
    [string]$Path = '.',
    [string[]]$Exclude = @(
'venv',
'venv*',
'.venv',
'.env',
'.git',
'node_modules',
'__pycache__',
'.vscode',
'_deps',
'*.dir',
'x64',
'.cache',
'.history',
'*.pyc',
'*.class'
    ),
    [int]$MaxDepth = -1,
    [switch]$DirectoriesOnly
)


function Get-Visible-Children {
    param($ParentPath)


    try {
        $items = Get-ChildItem -Path $ParentPath -Force -ErrorAction Stop


        $visible = $items | Where-Object {
            $include = $true
            foreach ($ex in $Exclude) {
                if ($_.Name -like $ex) { $include = $false; break }
            }
            if ($DirectoriesOnly) { $include = $include -and $_.PSIsContainer }
            $include
        } | Sort-Object @{Expression = { $_.PSIsContainer }; Descending = $true}, Name


        return ,$visible
    }
    catch {
        Write-Warning "Cannot access '$ParentPath': $($_.Exception.Message)"
        return @()
    }
}


function Print-Tree {
    param(
        [string]$TargetPath,
        [string]$Indent,
        [int]$Depth
    )


    $children = Get-Visible-Children -ParentPath $TargetPath
    for ($i = 0; $i -lt $children.Count; $i++) {
        $child = $children[$i]
        $isLast = ($i -eq ($children.Count - 1))
        $prefix = if ($isLast) { '└── ' } else { '├── ' }


        Write-Host "$Indent$prefix$($child.Name)"


        if ($child.PSIsContainer) {
            if (($MaxDepth -ne -1) -and ($Depth -ge $MaxDepth)) {
                continue
            }


            # ← 互換性のために明示的に if/else で nextIndent を作る
            if ($isLast) {
                $nextIndent = $Indent + '    '
            } else {
                $nextIndent = $Indent + '│   '
            }


            Print-Tree -TargetPath $child.FullName -Indent $nextIndent -Depth ($Depth + 1)
        }
    }
}


# 実行
$resolved = Resolve-Path -Path $Path
Write-Host $resolved.Path
Print-Tree -TargetPath $resolved.Path -Indent "" -Depth 1




























# # sp_tree_json


# # 概要:
# #   指定したフォルダ構造を JSON 化して出力し、指定した拡張子のファイルについては
# #   先頭 N 行を "preview" として一緒に含めます。生成AI に渡す用途に最適化しています。


# # 互換性:
# #   PowerShell 5.1 以上で動作するように記述しています（PowerShell 7 でも動作します）。


# # 使い方例:
# #   # 現在フォルダを JSON で出力（標準出力）
# #   .\sp_tree_json_preview.ps1


# #   # プロジェクトを除外パターン付きで JSON に書き出す
# #   .\sp_tree_json_preview.ps1 -Path .\myproject -Exclude @('*.vvm','node_modules','*.dll') -OutFile project_tree.json


# #   # .py と .md の先頭 5 行を取得し、最大プレビューサイズ 2MB に制限
# #   .\sp_tree_json_preview.ps1 -PreviewExtensions @('.py','.md') -PreviewLines 5 -MaxPreviewSizeMB 2 -OutFile tree.json


# # パラメータ:
# #   -Path                : 対象ディレクトリ (既定 '.')
# #   -Exclude             : 除外パターン配列 (ワイルドカード可)
# #   -MaxDepth            : 深さ制限 (-1 = 無制限)
# #   -DirectoriesOnly     : ディレクトリのみ出力
# #   -PreviewExtensions   : 先頭行を取得するファイル拡張子リスト
# #   -PreviewLines        : 取得する先頭行数
# #   -MaxPreviewSizeMB    : プレビューを作る最大ファイルサイズ（MB）
# #   -OutFile             : ファイルに書き出す場合の出力先パス（未指定で標準出力）
# #   -RelativePaths       : JSON 内のパスをルートからの相対パスにする


# # 出力 JSON の各ノードの主なキー:
# #   name          : ファイル/フォルダ名
# #   type          : "directory" または "file"
# #   relativePath  : ルートからの相対パス（-RelativePaths の場合）
# #   size          : バイト（ファイルのみ）
# #   modified      : 最終更新日時 (ISO 8601)
# #   children      : 子ノードの配列（ディレクトリのみ）
# #   preview       : 先頭 N 行 (文字列) または null


# # 注意:
# #   - バイナリや読み取り権限がないファイルは preview が null になります。
# #   - 非常に大きなディレクトリを JSON にする場合、出力サイズが巨大になるので -Exclude で絞ることを推奨します。
# # #>


# # 概要:
# #   指定したフォルダ構造を JSON 化して出力し、指定した拡張子のファイルについては
# #   先頭 N 行を "preview" として一緒に含めます。
# #   Git の状態（管理下、ステージ済み、変更あり等）によるフィルタリングに対応しました。

# # 使い方例:
# #   1. すべてのファイル (従来通り)
# #      .\sp_tree_json_git.ps1
# #
# #   2. Git管理下のファイルのみ (ゴミファイルや ignore されたものを除外)
# #      .\sp_tree_json_git.ps1 -GitFilter Tracked
# #
# #   3. ステージングした (git add した) ファイルのみ
# #      .\sp_tree_json_git.ps1 -GitFilter Staged
# #
# #   4. 変更があるファイル (編集中のもの) のみ
# #      .\sp_tree_json_git.ps1 -GitFilter Modified

# # パラメータ:
# #   -GitFilter           : 出力対象の絞り込み (None, Tracked, Staged, Modified)
# #   (その他は以前と同じ)
# #

# param(
#     [string]$Path = '.',
#     [string[]]$Exclude = @(
#         'venv*', '.venv', '.env', '.git', 'node_modules', '__pycache__', '.vscode', 
#         '_deps', '*.dir', 'x64', '.cache', '.history', '*.pyc', '*.class', 'treePowerShell.ps1'
#     ),
#     [int]$MaxDepth = -1,
#     [switch]$DirectoriesOnly,
#     [string[]]$PreviewExtensions = @('.md', '.py', '.txt', '.json', '.yaml', '.yml', '.c', '.h', '.java', '.html', '.js', '.jsx', '.ts', '.tsx'),
#     [int]$PreviewLines = 1000,
#     [int]$MaxPreviewSizeMB = 1,
#     [string]$OutFile = '',
#     [switch]$RelativePaths,
    
#     [ValidateSet('None', 'Tracked', 'Staged', 'Modified')]
#     [string]$GitFilter = 'None'
# )

# $Global:GitAllowedPaths = $null

# function Get-Git-File-List {
#     param([string]$RootPath, [string]$Mode)
    
#     if (-not (Test-Path (Join-Path $RootPath ".git"))) {
#         Write-Warning "指定されたパス '$RootPath' は Git リポジトリのルートではない可能性がありますが、処理を続行します。"
#     }

#     $files = @()
#     $currentDir = Get-Location
#     Set-Location $RootPath
    
#     try {
#         [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

#         # 修正箇所: @(...) で囲むことで、結果が1件でも0件でも必ず配列として扱います
#         if ($Mode -eq 'Tracked') {
#             $files = @(git ls-files)
#         }
#         elseif ($Mode -eq 'Staged') {
#             $files = @(git diff --name-only --cached)
#         }
#         elseif ($Mode -eq 'Modified') {
#             # 各コマンドの結果も配列化してから結合します
#             $f1 = @(git diff --name-only)
#             $f2 = @(git diff --name-only --cached)
#             $f3 = @(git ls-files --others --exclude-standard)
            
#             $files = $f1 + $f2 + $f3
#         }
#     }
#     catch {
#         Write-Error "Git コマンドの実行に失敗しました。"
#     }
#     finally {
#         Set-Location $currentDir
#     }

#     return $files | Select-Object -Unique
# }

# function Prepare-Git-Whitelist {
#     param([string]$RootPath)

#     if ($GitFilter -eq 'None') { return }

#     Write-Host "Git Filter Mode: [$GitFilter] - ファイルリストを取得中..." -ForegroundColor Cyan

#     $gitFiles = Get-Git-File-List -RootPath $RootPath -Mode $GitFilter
    
#     $Global:GitAllowedPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

#     foreach ($gf in $gitFiles) {
#         if ([string]::IsNullOrWhiteSpace($gf)) { continue }

#         $normalized = $gf -replace '/', [IO.Path]::DirectorySeparatorChar
#         $fullPath = Join-Path $RootPath $normalized
        
#         [void]$Global:GitAllowedPaths.Add($fullPath)

#         $parent = [IO.Path]::GetDirectoryName($fullPath)
#         while ($parent -and $parent.Length -ge $RootPath.Length) {
#             if ($Global:GitAllowedPaths.Contains($parent)) { break }
#             [void]$Global:GitAllowedPaths.Add($parent)
#             $parent = [IO.Path]::GetDirectoryName($parent)
#         }
#     }
    
#     Write-Host "対象ファイル数: $($gitFiles.Count)" -ForegroundColor Cyan
# }

# function Get-Visible-Children {
#     param(
#         [string]$ParentPath
#     )

#     try {
#         $items = Get-ChildItem -Path $ParentPath -Force -ErrorAction Stop
#     }
#     catch {
#         Write-Warning "Cannot access '$ParentPath': $($_.Exception.Message)"
#         return @()
#     }

#     $visible = @()
#     foreach ($it in $items) {
#         $excludeHit = $false
#         foreach ($ex in $Exclude) {
#             if ($it.Name -like $ex) {
#                 $excludeHit = $true
#                 break
#             }
#         }
#         if ($excludeHit) { continue }

#         if ($DirectoriesOnly -and -not $it.PSIsContainer) {
#             continue
#         }

#         if ($Global:GitAllowedPaths -ne $null) {
#             if (-not $Global:GitAllowedPaths.Contains($it.FullName)) {
#                 continue
#             }
#         }

#         $visible += $it
#     }

#     $visible = $visible | Sort-Object @{Expression = { $_.PSIsContainer }; Descending = $true }, Name
#     return , $visible
# }

# function Get-PreviewText {
#     param(
#         [string]$FilePath
#     )

#     try {
#         $fi = Get-Item -LiteralPath $FilePath -ErrorAction Stop
#     }
#     catch {
#         return $null
#     }

#     if (-not $fi -or $fi.Length -eq $null) { return $null }

#     $maxBytes = $MaxPreviewSizeMB * 1MB
#     if ($fi.Length -gt $maxBytes) { return $null }

#     try {
#         $lines = Get-Content -LiteralPath $FilePath -Encoding UTF8 -TotalCount $PreviewLines -ErrorAction Stop
#         return ($lines -join "`n")
#     }
#     catch {
#         try {
#             $lines = Get-Content -LiteralPath $FilePath -TotalCount $PreviewLines -ErrorAction Stop
#             return ($lines -join "`n")
#         }
#         catch {
#             return $null
#         }
#     }
# }

# function Build-Node {
#     param(
#         [string]$FullPath,
#         [int]$Depth
#     )

#     try {
#         $item = Get-Item -LiteralPath $FullPath -Force -ErrorAction Stop
#     }
#     catch {
#         return $null
#     }

#     $node = [ordered]@{}
#     $node.name = $item.Name
#     if ($RelativePaths) {
#         $root = (Resolve-Path -Path $Path).Path
#         if ($FullPath -like "$root*" ) {
#             $rel = $FullPath.Substring($root.Length)
#             if ($rel.StartsWith('\') -or $rel.StartsWith('/')) { $rel = $rel.Substring(1) }
#             $node.relativePath = $rel
#         }
#         else {
#             $node.relativePath = $FullPath
#         }
#     }
#     else {
#         $node.relativePath = $FullPath
#     }

#     if ($item.PSIsContainer) {
#         $node.type = 'directory'
#         $node.size = $null
#         $node.modified = $item.LastWriteTime.ToString('o')
#         $node.preview = $null

#         if (($MaxDepth -ne -1) -and ($Depth -ge $MaxDepth)) {
#             $node.children = @()
#             return $node
#         }

#         $children = Get-Visible-Children -ParentPath $FullPath
#         $childNodes = @()
#         foreach ($ch in $children) {
#             $childNode = Build-Node -FullPath $ch.FullName -Depth ($Depth + 1)
#             if ($childNode -ne $null) { $childNodes += $childNode }
#         }
#         $node.children = $childNodes
#     }
#     else {
#         $node.type = 'file'
#         $node.size = $item.Length
#         $node.modified = $item.LastWriteTime.ToString('o')

#         $ext = [IO.Path]::GetExtension($item.Name)
#         if ($ext -ne $null) { $ext = $ext.ToLower() }

#         $node.preview = $null
#         if ($PreviewExtensions -contains $ext) {
#             $pv = Get-PreviewText -FilePath $FullPath
#             if ($pv -ne $null) { $node.preview = $pv }
#         }

#         $node.children = @()
#     }

#     return $node
# }

# # --- 実行ブロック ---

# $resolvedRoot = Resolve-Path -Path $Path
# $rootPath = $resolvedRoot.Path

# Prepare-Git-Whitelist -RootPath $rootPath

# $rootNode = Build-Node -FullPath $rootPath -Depth 0

# $json = $null
# try {
#     $json = $rootNode | ConvertTo-Json -Depth 100 -Compress
# }
# catch {
#     $json = $rootNode | ConvertTo-Json -Depth 50 -Compress
# }

# if ($OutFile -ne '') {
#     $json | Out-File -FilePath $OutFile -Encoding UTF8
#     Write-Output "Wrote JSON to: $OutFile"
# }
# else {
#     Write-Output $json
# }






# <#
# sp_tree_json_optimized

# 概要:
#   LLM共有用にJSON構造を極限まで軽量化したバージョンです。
#   メタデータ（サイズ、日付、冗長なパス）を削除し、
#   ファイル名、ディレクトリ構造、プレビューのみを出力します。

# #>

# param(
#     [string]$Path = '.',
#     [string[]]$Exclude = @(
#         'venv*', '.venv', '.env', '.git', 'node_modules', '__pycache__', '.vscode', 
#         '_deps', '*.dir', 'x64', '.cache', '.history', '*.pyc', '*.class', 'treePowerShell.ps1'
#     ),
#     [int]$MaxDepth = -1,
#     [switch]$DirectoriesOnly,
#     [string[]]$PreviewExtensions = @('.md', '.py', '.txt', '.json', '.yaml', '.yml', '.c', '.h', '.java', '.html', '.js', '.jsx', '.ts', '.tsx'),
#     [int]$PreviewLines = 1000,
#     [int]$MaxPreviewSizeMB = 1,
#     [string]$OutFile = '',
#     # RelativePaths は廃止しましたが、互換性のため残し無視します
#     [switch]$RelativePaths, 
    
#     [ValidateSet('None', 'Tracked', 'Staged', 'Modified')]
#     [string]$GitFilter = 'None'
# )

# # デバッグ出力を有効にする設定（実行時に -Debug をつけなくても表示させたい場合はコメントアウトを外す）
# # $DebugPreference = "Continue"

# $Global:GitAllowedPaths = $null

# function Get-Git-File-List {
#     param([string]$RootPath, [string]$Mode)
    
#     if (-not (Test-Path (Join-Path $RootPath ".git"))) {
#         Write-Warning "指定されたパス '$RootPath' は Git リポジトリのルートではない可能性があります。"
#     }

#     $files = @()
#     $currentDir = Get-Location
#     Set-Location $RootPath
    
#     try {
#         [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
#         Write-Host "Executing Git commands for filter: $Mode" -ForegroundColor Gray

#         if ($Mode -eq 'Tracked') {
#             $files = @(git ls-files)
#         }
#         elseif ($Mode -eq 'Staged') {
#             $files = @(git diff --name-only --cached)
#         }
#         elseif ($Mode -eq 'Modified') {
#             $f1 = @(git diff --name-only)
#             $f2 = @(git diff --name-only --cached)
#             $f3 = @(git ls-files --others --exclude-standard)
#             $files = $f1 + $f2 + $f3
#         }
#     }
#     catch {
#         Write-Error "Git コマンドの実行に失敗しました。"
#     }
#     finally {
#         Set-Location $currentDir
#     }

#     return $files | Select-Object -Unique
# }

# function Prepare-Git-Whitelist {
#     param([string]$RootPath)

#     if ($GitFilter -eq 'None') { return }

#     Write-Host "Git Filter Mode: [$GitFilter] - ファイルリストを取得中..." -ForegroundColor Cyan

#     $gitFiles = Get-Git-File-List -RootPath $RootPath -Mode $GitFilter
    
#     $Global:GitAllowedPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

#     foreach ($gf in $gitFiles) {
#         if ([string]::IsNullOrWhiteSpace($gf)) { continue }

#         $normalized = $gf -replace '/', [IO.Path]::DirectorySeparatorChar
#         $fullPath = Join-Path $RootPath $normalized
        
#         [void]$Global:GitAllowedPaths.Add($fullPath)

#         $parent = [IO.Path]::GetDirectoryName($fullPath)
#         while ($parent -and $parent.Length -ge $RootPath.Length) {
#             if ($Global:GitAllowedPaths.Contains($parent)) { break }
#             [void]$Global:GitAllowedPaths.Add($parent)
#             $parent = [IO.Path]::GetDirectoryName($parent)
#         }
#     }
    
#     Write-Host "対象ファイル数: $($gitFiles.Count)" -ForegroundColor Cyan
# }

# function Get-Visible-Children {
#     param(
#         [string]$ParentPath
#     )

#     try {
#         $items = Get-ChildItem -Path $ParentPath -Force -ErrorAction Stop
#     }
#     catch {
#         Write-Warning "Cannot access '$ParentPath': $($_.Exception.Message)"
#         return @()
#     }

#     $visible = @()
#     foreach ($it in $items) {
#         $excludeHit = $false
#         foreach ($ex in $Exclude) {
#             if ($it.Name -like $ex) {
#                 $excludeHit = $true
#                 break
#             }
#         }
#         if ($excludeHit) { continue }

#         if ($DirectoriesOnly -and -not $it.PSIsContainer) {
#             continue
#         }

#         if ($Global:GitAllowedPaths -ne $null) {
#             if (-not $Global:GitAllowedPaths.Contains($it.FullName)) {
#                 continue
#             }
#         }

#         $visible += $it
#     }

#     $visible = $visible | Sort-Object @{Expression = { $_.PSIsContainer }; Descending = $true }, Name
#     return , $visible
# }

# function Get-PreviewText {
#     param(
#         [string]$FilePath
#     )

#     try {
#         $fi = Get-Item -LiteralPath $FilePath -ErrorAction Stop
#     }
#     catch {
#         return $null
#     }

#     if (-not $fi -or $fi.Length -eq $null) { return $null }

#     $maxBytes = $MaxPreviewSizeMB * 1MB
#     if ($fi.Length -gt $maxBytes) { 
#         Write-Host "Skipping preview for large file: $($fi.Name) ($($fi.Length/1MB) MB)" -ForegroundColor DarkGray
#         return $null 
#     }

#     try {
#         $lines = Get-Content -LiteralPath $FilePath -Encoding UTF8 -TotalCount $PreviewLines -ErrorAction Stop
#         return ($lines -join "`n")
#     }
#     catch {
#         # Fallback for different encodings or errors
#         try {
#             $lines = Get-Content -LiteralPath $FilePath -TotalCount $PreviewLines -ErrorAction Stop
#             return ($lines -join "`n")
#         }
#         catch {
#             return $null
#         }
#     }
# }

# function Build-Node {
#     param(
#         [string]$FullPath,
#         [int]$Depth
#     )

#     try {
#         $item = Get-Item -LiteralPath $FullPath -Force -ErrorAction Stop
#     }
#     catch {
#         Write-Debug "Error accessing item: $FullPath"
#         return $null
#     }

#     # --- 最適化変更点 Start ---
#     # メタデータ(size, modified, relativePath, type)を排除
#     $node = [ordered]@{
#         name = $item.Name
#     }

#     if ($item.PSIsContainer) {
#         # ディレクトリ
#         if (($MaxDepth -ne -1) -and ($Depth -ge $MaxDepth)) {
#             $node.children = @()
#             return $node
#         }

#         $children = Get-Visible-Children -ParentPath $FullPath
#         $childNodes = @()
#         foreach ($ch in $children) {
#             $childNode = Build-Node -FullPath $ch.FullName -Depth ($Depth + 1)
#             if ($childNode -ne $null) { $childNodes += $childNode }
#         }
#         # ディレクトリ識別用に children キーを持たせる
#         $node.children = $childNodes
#     }
#     else {
#         # ファイル
#         # children は持たせない
#         # preview がある場合のみキーを追加

#         $ext = [IO.Path]::GetExtension($item.Name)
#         if ($ext -ne $null) { $ext = $ext.ToLower() }

#         if ($PreviewExtensions -contains $ext) {
#             $pv = Get-PreviewText -FilePath $FullPath
#             if ($pv -ne $null) { 
#                 $node.preview = $pv 
#             }
#         }
#     }
#     # --- 最適化変更点 End ---

#     return $node
# }

# # --- 実行ブロック ---

# $resolvedRoot = Resolve-Path -Path $Path
# $rootPath = $resolvedRoot.Path

# Write-Host "Target Root: $rootPath" -ForegroundColor Green

# Prepare-Git-Whitelist -RootPath $rootPath

# $rootNode = Build-Node -FullPath $rootPath -Depth 0

# $json = $null
# try {
#     # Depth は階層の深さではなくオブジェクトの展開深さなので大きめに確保
#     $json = $rootNode | ConvertTo-Json -Depth 100 -Compress
# }
# catch {
#     Write-Warning "JSON変換中にエラーが発生しました。深度を減らして再試行します。"
#     $json = $rootNode | ConvertTo-Json -Depth 50 -Compress
# }

# if ($OutFile -ne '') {
#     $json | Out-File -FilePath $OutFile -Encoding UTF8
#     Write-Host "JSON Output saved to: $OutFile" -ForegroundColor Cyan
# }
# else {
#     # 標準出力に書き出し
#     Write-Output $json
# }








# # sp_tree_json

# # 概要:
# #   指定したフォルダ構造を JSON 化して出力し、指定した拡張子のファイルについては
# #   先頭 N 行を "preview" として一緒に含めます。生成AI に渡す用途に最適化しています。
# #   さらに、指定された TOON ツールを利用して .toon 形式のファイルも生成します。

# # 互換性:
# #   PowerShell 5.1 以上

# # 使い方例:
# #   .\treePowerShell.ps1 -PreviewExtensions @('.py','.md') -OutFile project.json
# # .\treePowerShell.ps1 -o tree.json
# param(
#     [string]$Path = '.',
#     [string[]]$Exclude = @(
#                 'venv',
#         'venv*',
#         '.venv','.env',
#         '.git',
#         'node_modules',
#         '__pycache__',
#         '.vscode',
#         '_deps',
#         '*.dir',
#         'x64',
#         '.cache',
#         '.history', '*.pyc', '*.class','treePowerShell.ps1'
#     ),
#     [int]$MaxDepth = -1,
#     [switch]$DirectoriesOnly,
#     [string[]]$PreviewExtensions = @('.md', '.py', '.txt', '.json', '.yaml', '.yml','.c','.h','.java','.html','.js','.jsx','.ts','.tsx'),
#     [int]$PreviewLines = 1000,
#     [int]$MaxPreviewSizeMB = 1,
#     [string]$OutFile = '',
#     [switch]$RelativePaths
# )

# # --- 設定: TOONツールのパス ---
# # インストール先のパス
# $ToonRepoPath = "C:\Users\yusei\Desktop\LLMcontext\toon-python"
# # uv sync で作成された仮想環境内の実行ファイルを指定
# $ToonExe = Join-Path $ToonRepoPath ".venv\Scripts\toon.exe"
# # -----------------------------

# function Get-Visible-Children {
#     param(
#         [string]$ParentPath
#     )

#     try {
#         $items = Get-ChildItem -Path $ParentPath -Force -ErrorAction Stop
#     }
#     catch {
#         Write-Warning "Cannot access '$ParentPath': $($_.Exception.Message)"
#         return @()
#     }

#     $visible = @()
#     foreach ($it in $items) {
#         $include = $true
#         foreach ($ex in $Exclude) {
#             if ($it.Name -like $ex) {
#                 $include = $false
#                 break
#             }
#         }
#         if ($DirectoriesOnly -and -not $it.PSIsContainer) {
#             $include = $false
#         }
#         if ($include) { $visible += $it }
#     }

#     # ディレクトリを先に、その後名前順
#     $visible = $visible | Sort-Object @{Expression = { $_.PSIsContainer }; Descending = $true}, Name
#     return ,$visible
# }

# function Get-PreviewText {
#     param(
#         [string]$FilePath
#     )

#     try {
#         $fi = Get-Item -LiteralPath $FilePath -ErrorAction Stop
#     }
#     catch {
#         return $null
#     }

#     if (-not $fi -or $fi.Length -eq $null) { return $null }

#     $maxBytes = $MaxPreviewSizeMB * 1MB
#     if ($fi.Length -gt $maxBytes) { return $null }

#     try {
#         # まず UTF8 で読んでみる
#         $lines = Get-Content -LiteralPath $FilePath -Encoding UTF8 -TotalCount $PreviewLines -ErrorAction Stop
#         return ($lines -join "`n")
#     }
#     catch {
#         try {
#             # 失敗したら既定のエンコーディングで再試行
#             $lines = Get-Content -LiteralPath $FilePath -TotalCount $PreviewLines -ErrorAction Stop
#             return ($lines -join "`n")
#         }
#         catch {
#             return $null
#         }
#     }
# }

# function Build-Node {
#     param(
#         [string]$FullPath,
#         [int]$Depth
#     )

#     try {
#         $item = Get-Item -LiteralPath $FullPath -Force -ErrorAction Stop
#     }
#     catch {
#         return $null
#     }

#     $node = [ordered]@{}
#     $node.name = $item.Name
#     if ($RelativePaths) {
#         $root = (Resolve-Path -Path $Path).Path
#         if ($FullPath -like "$root*" ) {
#             $rel = $FullPath.Substring($root.Length)
#             if ($rel.StartsWith('\') -or $rel.StartsWith('/')) { $rel = $rel.Substring(1) }
#             $node.relativePath = $rel
#         }
#         else {
#             $node.relativePath = $FullPath
#         }
#     }
#     else {
#         $node.relativePath = $FullPath
#     }

#     if ($item.PSIsContainer) {
#         $node.type = 'directory'
#         $node.size = $null
#         $node.modified = $item.LastWriteTime.ToString('o')
#         $node.preview = $null

#         # 深度チェック
#         if (($MaxDepth -ne -1) -and ($Depth -ge $MaxDepth)) {
#             $node.children = @()
#             return $node
#         }

#         $children = Get-Visible-Children -ParentPath $FullPath
#         $childNodes = @()
#         foreach ($ch in $children) {
#             $childNode = Build-Node -FullPath $ch.FullName -Depth ($Depth + 1)
#             # $childNode -ne $null
#             if ($childNode -ne $null) { $childNodes += $childNode }
#         }
#         $node.children = $childNodes
#     }
#     else {
#         $node.type = 'file'
#         $node.size = $item.Length
#         $node.modified = $item.LastWriteTime.ToString('o')

#         $ext = [IO.Path]::GetExtension($item.Name)
#         if ($ext -ne $null) { $ext = $ext.ToLower() }

#         $node.preview = $null
#         if ($PreviewExtensions -contains $ext) {
#             $pv = Get-PreviewText -FilePath $FullPath
#             if ($pv -ne $null) { $node.preview = $pv }
#         }

#         $node.children = @()
#     }

#     return $node
# }

# # --- メイン実行ブロック ---
# $resolvedRoot = Resolve-Path -Path $Path
# $rootPath = $resolvedRoot.Path

# $rootNode = Build-Node -FullPath $rootPath -Depth 0

# # JSON に変換
# $json = $null
# try {
#     $json = $rootNode | ConvertTo-Json -Depth 100 -Compress
# }
# catch {
#     # 万一深さで失敗したらもう少し小さい深さで試す
#     $json = $rootNode | ConvertTo-Json -Depth 50 -Compress
# }

# if ($OutFile -ne '') {
#     # 1. JSONファイルの書き出し
#     $json | Out-File -FilePath $OutFile -Encoding UTF8
#     Write-Output "Wrote JSON to: $OutFile"

#     # 2. TOON形式への変換処理
#     if (Test-Path $ToonExe) {
#         # 拡張子を .toon に変更
#         $ToonOutFile = [System.IO.Path]::ChangeExtension($OutFile, ".toon")
        
#         Write-Host "Converting JSON to TOON format..." -ForegroundColor Cyan
        
#         # toonコマンドの実行
#         # 引数: 入力JSONパス -o 出力TOONパス
#         $process = Start-Process -FilePath $ToonExe -ArgumentList "`"$OutFile`" -o `"$ToonOutFile`"" -Wait -NoNewWindow -PassThru
        
#         if ($process.ExitCode -eq 0) {
#             Write-Host "Wrote TOON to: $ToonOutFile" -ForegroundColor Green
#         }
#         else {
#             Write-Warning "TOON conversion failed. ExitCode: $($process.ExitCode)"
#         }
#     }
#     else {
#         Write-Warning "TOON executable not found at: $ToonExe"
#         Write-Warning "Skipping TOON conversion."
#     }
# }
# else {
#     # OutFile指定がない場合は標準出力にJSONを出すだけ（TOON変換はしない）
#     Write-Output $json
# }

