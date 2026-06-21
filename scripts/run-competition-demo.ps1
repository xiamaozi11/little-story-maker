# 小小故事家 — 比赛终端演示启动脚本
# 用法:
#   .\scripts\run-competition-demo.ps1              # 演示模式（不调 API，适合彩排录屏）
#   .\scripts\run-competition-demo.ps1 -Live        # 真实 API
#   .\scripts\run-competition-demo.ps1 -Live -Pause # 逐步暂停录屏
#   .\scripts\run-competition-demo.ps1 -Live -Pause -SkipImage -Scenes 2
param(
    [switch]$Live,
    [switch]$Pause,
    [switch]$SkipImage,
    [int]$Scenes = 3
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

$PythonCandidates = @(
    "$env:USERPROFILE\miniconda3\python.exe",
    "$env:USERPROFILE\anaconda3\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "python",
    "py"
)

$Python = $PythonCandidates | Where-Object {
    if ($_ -in @("python", "py")) {
        $cmd = Get-Command $_ -ErrorAction SilentlyContinue
        return [bool]$cmd
    }
    return Test-Path $_
} | Select-Object -First 1

if (-not $Python) {
    Write-Host "未找到 Python，请安装 Python 3.10+ 或 Miniconda" -ForegroundColor Red
    exit 1
}

Write-Host "Python: $Python" -ForegroundColor Cyan
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 | Out-Null
Set-Location $Root

$argsList = @("scripts/demo_competition.py")
if ($Live) { $argsList += "--live" }
if ($Pause) { $argsList += "--pause" }
if ($SkipImage) { $argsList += "--skip-image" }
$argsList += @("--scenes", "$Scenes")

& $Python @argsList
exit $LASTEXITCODE
