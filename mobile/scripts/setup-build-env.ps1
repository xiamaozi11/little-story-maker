# 下载 JDK 17 + Android SDK 命令行工具（首次打包需运行一次）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Tools = Join-Path $Root "tools"
$JdkDir = Join-Path $Tools "jdk-17.0.2"
if (-not (Test-Path "$JdkDir\bin\java.exe")) {
  $JdkDir = Join-Path $Tools "jdk-17"
}
$SdkDir = Join-Path $Tools "android-sdk"
$Cache = Join-Path $Tools "cache"
New-Item -ItemType Directory -Force -Path $Cache, $Tools, $SdkDir | Out-Null

function Download-File($Url, $Dest) {
  if (Test-Path $Dest) { Write-Host "[跳过] 已存在: $Dest"; return }
  Write-Host "[下载] $Url"
  Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing
}

# --- JDK 17 (华为镜像) ---
$JdkZip = Join-Path $Cache "openjdk-17.zip"
if (-not (Test-Path "$JdkDir\bin\java.exe")) {
  Download-File "https://mirrors.huaweicloud.com/openjdk/17.0.2/openjdk-17.0.2_windows-x64_bin.zip" $JdkZip
  Write-Host "[解压] JDK 17..."
  Expand-Archive -Path $JdkZip -DestinationPath $Tools -Force
  $JdkDir = Get-ChildItem $Tools -Directory | Where-Object { $_.Name -like "jdk-17*" -or $_.Name -like "openjdk*" } | Select-Object -First 1
  if ($JdkDir) { $JdkDir = $JdkDir.FullName }
}

$Java = Join-Path $JdkDir "bin\java.exe"
& $Java -version

# --- Android SDK commandlinetools ---
$CmdlineZip = Join-Path $Cache "cmdline-tools.zip"
$CmdlineRoot = Join-Path $SdkDir "cmdline-tools\latest"
if (-not (Test-Path "$CmdlineRoot\bin\sdkmanager.bat")) {
  Download-File "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip" $CmdlineZip
  $TmpCmd = Join-Path $Cache "cmdline-tmp"
  if (Test-Path $TmpCmd) { Remove-Item $TmpCmd -Recurse -Force }
  Expand-Archive -Path $CmdlineZip -DestinationPath $TmpCmd -Force
  New-Item -ItemType Directory -Force -Path (Split-Path $CmdlineRoot) | Out-Null
  if (Test-Path $CmdlineRoot) { Remove-Item $CmdlineRoot -Recurse -Force -ErrorAction SilentlyContinue }
  New-Item -ItemType Directory -Force -Path $CmdlineRoot | Out-Null
  robocopy (Join-Path $TmpCmd "cmdline-tools") $CmdlineRoot /E /NFL /NDL /NJH /NJS | Out-Null
}

$env:JAVA_HOME = $JdkDir
$env:ANDROID_HOME = $SdkDir
$sdkmanager = Join-Path $CmdlineRoot "bin\sdkmanager.bat"

# --- 接受 SDK 许可证 ---
$LicDir = Join-Path $SdkDir "licenses"
New-Item -ItemType Directory -Force -Path $LicDir | Out-Null
$licenseHashes = @{
  "android-sdk-license" = "24333f8a63b6825ea9c5514f83c282f4219162e"
  "android-sdk-preview-license" = "84831b9409646a918e30573bab4c9c91346d7abd"
  "android-sdk-arm-dbf-license" = "859f317696749be334479c927076b933"
  "intel-android-extra-license" = "d975f751698a77b662f1254ddbeac39012e52445"
  "google-gdk-license" = "33b6a2b64607f4b1177733645923911ee374841"
}
foreach ($name in $licenseHashes.Keys) {
  [System.IO.File]::WriteAllText((Join-Path $LicDir $name), $licenseHashes[$name])
}

Write-Host "[安装] Android SDK 组件（约 500MB，需稳定网络）..."
$packages = @(
  "platform-tools",
  "platforms;android-35",
  "build-tools;35.0.0"
)
$yes = ("y`n" * 20)
$yes | & $sdkmanager --sdk_root=$SdkDir @packages 2>&1

Write-Host ""
Write-Host "========================================"
Write-Host " 环境就绪，请运行:"
Write-Host "   mobile\scripts\build-apk.bat"
Write-Host "========================================"
