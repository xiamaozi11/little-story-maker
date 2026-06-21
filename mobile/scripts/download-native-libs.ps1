# 下载 MNN sherpa-mnn 本地库到 jniLibs（libMNN.so + libsherpa-mnn-jni.so）
$ErrorActionPreference = "Stop"
$MobileRoot = Split-Path $PSScriptRoot -Parent
$JniDir = Join-Path $MobileRoot "android\app\src\main\jniLibs\arm64-v8a"
$Url = "https://meta.alicdn.com/data/mnn/avatar/native-libs-arm64-v8a.zip"
$Zip = Join-Path $env:TEMP "sherpa-mnn-native-libs-arm64-v8a.zip"
$Extract = Join-Path $env:TEMP "sherpa-mnn-native-libs"

$Required = @(
    "libsherpa-mnn-jni.so",
    "libMNN.so",
    "libnnrruntime.so"
)

$allPresent = $true
foreach ($name in $Required) {
    $path = Join-Path $JniDir $name
    if (-not ((Test-Path $path) -and ((Get-Item $path).Length -gt 0))) {
        $allPresent = $false
        break
    }
}
if ($allPresent) {
    Write-Host "Native libs already present in $JniDir" -ForegroundColor DarkGray
    exit 0
}

Write-Host "Downloading MNN native libs..."
Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing -TimeoutSec 600

if (Test-Path $Extract) { Remove-Item $Extract -Recurse -Force }
Expand-Archive -Path $Zip -DestinationPath $Extract -Force
Remove-Item $Zip -Force

New-Item -ItemType Directory -Force -Path $JniDir | Out-Null

$Sources = @(
    (Join-Path $Extract "app\src\main\jniLibs\arm64-v8a"),
    (Join-Path $Extract "app\src\main\libs\MNN\lib\arm64-v8a"),
    (Join-Path $Extract "app\src\main\libs\NNR\lib\arm64-v8a")
)
foreach ($src in $Sources) {
    if (Test-Path $src) {
        Copy-Item (Join-Path $src "*.so") $JniDir -Force
    }
}

foreach ($name in $Required) {
    $path = Join-Path $JniDir $name
    if (-not (Test-Path $path)) {
        Write-Host "ERROR: missing $name" -ForegroundColor Red
        exit 1
    }
    $mb = [math]::Round((Get-Item $path).Length / 1MB, 2)
    Write-Host "OK $name ($mb MB)" -ForegroundColor Green
}

Write-Host "All native libs ready in $JniDir" -ForegroundColor Green
