# 下载 MNN ASR 模型到 Android assets（打包进 APK）
# 默认存到 D:\storycraft-asr-assets，通过目录联接挂到 assets，避免 E: 盘空间不足
$ErrorActionPreference = "Stop"
$MobileRoot = Split-Path $PSScriptRoot -Parent
$ModelSubDir = "sherpa-mnn-streaming-zipformer-bilingual-zh-en-2023-02-20"
$AssetDir = Join-Path $MobileRoot "android\app\src\main\assets\mnn-asr\$ModelSubDir"
$CacheRoot = if ($env:STORYCRAFT_ASR_CACHE) { $env:STORYCRAFT_ASR_CACHE } else { "D:\storycraft-asr-assets" }
$CacheDir = Join-Path $CacheRoot $ModelSubDir

$Files = @(
    "encoder-epoch-99-avg-1.int8.mnn",
    "decoder-epoch-99-avg-1.int8.mnn",
    "joiner-epoch-99-avg-1.int8.mnn",
    "tokens.txt"
)

$UrlBases = @(
    "https://modelscope.oss-cn-beijing.aliyuncs.com/MNN/sherpa-mnn-streaming-zipformer-bilingual-zh-en-2023-02-20",
    "https://huggingface.co/taobao-mnn/sherpa-mnn-streaming-zipformer-bilingual-zh-en-2023-02-20/resolve/main"
)

function Ensure-AssetJunction {
    param([string]$Target, [string]$Source)
    $parent = Split-Path $Target -Parent
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    if (Test-Path $Target) {
        $item = Get-Item $Target -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            if ($item.Target -eq $Source) {
                Write-Host "[skip] 目录联接已存在: $Target -> $Source" -ForegroundColor DarkGray
                return
            }
            cmd /c "rmdir `"$Target`"" | Out-Null
        } elseif ($item.PSIsContainer) {
            $hasFiles = Get-ChildItem $Target -File -ErrorAction SilentlyContinue
            if ($hasFiles) {
                Write-Host "[skip] assets 目录已有文件: $Target" -ForegroundColor DarkGray
                return
            }
            Remove-Item $Target -Recurse -Force
        } else {
            Remove-Item $Target -Force
        }
    }

    New-Item -ItemType Directory -Force -Path $Source | Out-Null
    cmd /c "mklink /J `"$Target`" `"$Source`"" | Out-Null
    Write-Host "ASR 模型目录联接: $Target -> $Source" -ForegroundColor Cyan
}

New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
Write-Host "ASR 模型目标目录: $CacheDir"

# 清理旧版 assets 路径（无 mnn-asr 前缀）
$LegacyAssetDir = Join-Path $MobileRoot "android\app\src\main\assets\$ModelSubDir"
if (Test-Path $LegacyAssetDir) {
    $legacy = Get-Item $LegacyAssetDir -Force
    if ($legacy.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        cmd /c "rmdir `"$LegacyAssetDir`"" | Out-Null
        Write-Host "[cleanup] 已移除旧版目录联接: $LegacyAssetDir" -ForegroundColor Yellow
    }
}

$allOk = $true
foreach ($name in $Files) {
    $target = Join-Path $CacheDir $name
    if ((Test-Path $target) -and ((Get-Item $target).Length -gt 0)) {
        $mb = [math]::Round((Get-Item $target).Length / 1MB, 2)
        Write-Host "[skip] $name ($mb MB)" -ForegroundColor DarkGray
        continue
    }

    Write-Host "[download] $name ..."
    $ok = $false
    foreach ($base in $UrlBases) {
        $url = "$base/$name"
        try {
            Invoke-WebRequest -Uri $url -OutFile "$target.part" -UseBasicParsing -TimeoutSec 600
            Move-Item -Force "$target.part" $target
            $mb = [math]::Round((Get-Item $target).Length / 1MB, 2)
            Write-Host "  OK $name ($mb MB) from $base" -ForegroundColor Green
            $ok = $true
            break
        } catch {
            Write-Host "  fail $url : $($_.Exception.Message)" -ForegroundColor Yellow
            if (Test-Path "$target.part") { Remove-Item "$target.part" -Force }
        }
    }
    if (-not $ok) {
        Write-Host "ERROR: 无法下载 $name" -ForegroundColor Red
        $allOk = $false
    }
}

if (-not $allOk) { exit 1 }

Ensure-AssetJunction -Target $AssetDir -Source $CacheDir

$totalMb = [math]::Round((Get-ChildItem $CacheDir | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Host ""
Write-Host "全部 ASR 模型已就绪，合计约 $totalMb MB" -ForegroundColor Green
