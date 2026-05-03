$ErrorActionPreference = "Continue"
$BaseDir = $PSScriptRoot
if (-not $BaseDir) { $BaseDir = (Get-Item .).FullName }
Set-Location $BaseDir
Write-Host "Working in: $BaseDir"

$folders = @("gradle\wrapper","app\src\main\assets","app\build\outputs\apk\debug")
foreach($f in $folders) {
    if (!(Test-Path $f)) { 
        Write-Host "Creating $f"
        New-Item -ItemType Directory -Path $f -Force | Out-Null 
    }
}

$JarUri = "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.jar"
$JarDst = "gradle\wrapper\gradle-wrapper.jar"
Write-Host "Getting jar..."
try {
    Invoke-WebRequest -Uri $JarUri -OutFile $JarDst -UseBasicParsing
    Write-Host "Got jar: $(Get-Item $JarDst).Length bytes"
} catch {
    Write-Host "ERROR: $_"
}

$PropUri = "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.properties"
$PropDst = "gradle\wrapper\gradle-wrapper.properties"
Invoke-WebRequest -Uri $PropUri -OutFile $PropDst -UseBasicParsing

Write-Host "Building..."
& java -classpath $JarDst org.gradle.wrapper.GradleWrapperMain assembleDebug
pause
