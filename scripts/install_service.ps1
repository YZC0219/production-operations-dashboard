$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) { throw "未找到虚拟环境，请先安装依赖。" }
& $PythonExe (Join-Path $PSScriptRoot "windows_service.py") --startup auto install
& $PythonExe (Join-Path $PSScriptRoot "windows_service.py") start
Write-Host "生产运营看板 Windows 服务已安装并启动。"
