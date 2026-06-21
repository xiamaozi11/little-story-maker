# 本地打包 Release APK
$ErrorActionPreference = "Stop"
$MobileRoot = Split-Path $PSScriptRoot -Parent
$JdkCandidates = @(
    "$MobileRoot\.tools\jdk-17.0.19+10",
    "$MobileRoot\tools\jdk-17.0.2",
    "$MobileRoot\.tools\jdk-17"
)
$JdkHome = $JdkCandidates | Where-Object { Test-Path "$_\bin\java.exe" } | Select-Object -First 1

if (-not $JdkHome) {
    Write-Host "JDK 17 not found. Install or extract to mobile\.tools\jdk-17.0.19+10" -ForegroundColor Yellow
    exit 1
}

$env:JAVA_HOME = $JdkHome
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
if (-not $env:GRADLE_USER_HOME) { $env:GRADLE_USER_HOME = "D:\gradle-cache-storycraft" }
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = "$MobileRoot\tools\android-sdk" }

Write-Host "JAVA_HOME=$env:JAVA_HOME"
Write-Host "GRADLE_USER_HOME=$env:GRADLE_USER_HOME"
& "$env:JAVA_HOME\bin\java.exe" -version

Write-Host ""
Write-Host "[1/4] Sync default settings from .env ..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$MobileRoot\scripts\sync-default-settings.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/4] Download ASR models ..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$MobileRoot\scripts\download-asr-models.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/4] Download native libs ..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$MobileRoot\scripts\download-native-libs.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/4] Gradle assembleRelease ..." -ForegroundColor Cyan
Push-Location "$MobileRoot\android"
try {
    .\gradlew.bat assembleRelease --no-daemon
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $apk = "app\build\outputs\apk\release\app-release.apk"
    $apkName = "StoryCraft-children-v1.0.4.apk"
    $dest = Join-Path $MobileRoot $apkName
    Copy-Item $apk $dest -Force
    $destD = Join-Path "D:\" $apkName
    Copy-Item $apk $destD -Force
    $mb = [math]::Round((Get-Item $dest).Length / 1MB, 2)
    Write-Host ""
    Write-Host "APK OK ($mb MB) — 安装名: 小小故事家 v1.0.4" -ForegroundColor Green
    Write-Host "  $dest"
    Write-Host "  $destD"
} finally {
    Pop-Location
}
