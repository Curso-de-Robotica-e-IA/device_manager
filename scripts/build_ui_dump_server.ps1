param(
    [Parameter(Mandatory = $true)]
    [string]$AndroidJar,
    [Parameter(Mandatory = $true)]
    [string]$D8Bat
)

$ErrorActionPreference = "Stop"
$buildDir = Join-Path $PSScriptRoot "..\build\ui_dump_server"
$assetsDir = Join-Path $PSScriptRoot "..\device_manager\assets"

New-Item -ItemType Directory -Force -Path $buildDir, $assetsDir | Out-Null

javac --release 11 -cp $AndroidJar -d $buildDir (Join-Path $PSScriptRoot "..\android_server\UiDumpServer.java")
& $D8Bat --output $assetsDir (Join-Path $buildDir "com\devicemanager\UiDumpServer.class")
Move-Item -Force (Join-Path $assetsDir "classes.dex") (Join-Path $assetsDir "dm_ui_dump.dex")

Write-Host "Built: $(Join-Path $assetsDir 'dm_ui_dump.dex')"
