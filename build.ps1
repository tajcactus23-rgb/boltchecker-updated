$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BaseDir

Write-Host "Base: $BaseDir"
New-Item -ItemType Directory -Force -Path "$BaseDir\gradle\wrapper" | Out-Null
New-Item -ItemType Directory -Force -Path "$BaseDir\app\src\main\assets" | Out-Null
New-Item -ItemType Directory -Force -Path "$BaseDir\app\build\outputs\apk\debug" | Out-Null
Write-Host "Folders done"

$JarPath = "$BaseDir\gradle\wrapper\gradle-wrapper.jar"
$PropPath = "$BaseDir\gradle\wrapper\gradle-wrapper.properties"

if (-not (Test-Path $JarPath)) {
    Write-Host "Downloading jar..."
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.jar" -OutFile $JarPath
}
if (-not (Test-Path $PropPath)) {
    Write-Host "Downloading properties..."
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.properties" -OutFile $PropPath
}

Write-Host "Building..."
& java -classpath $JarPath org.gradle.wrapper.GradleWrapperMain assembleDebug
Write-Host "Done"
pause
