$ErrorActionPreference = "Continue"
$BaseDir = $PSScriptRoot
if (-not $BaseDir) { $BaseDir = (Get-Item .).FullName }
Set-Location $BaseDir
Write-Host "BASE: $BaseDir"

# Create folders here, in the same folder as script
$folders = @("wrapper","assets","outputs\apk\debug")
foreach($f in $folders) {
    if (!(Test-Path $f)) { 
        Write-Host "Creating $f"
        New-Item -ItemType Directory -Path $f -Force | Out-Null 
    }
}

$JarDst = "wrapper\gradle-wrapper.jar"
$PropDst = "wrapper\gradle-wrapper.properties"

if (!(Test-Path $JarDst)) {
    Write-Host "Downloading wrapper..."
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.jar" -OutFile $JarDst -UseBasicParsing
}

if (!(Test-Path $PropDst)) {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.properties" -OutFile $PropDst -UseBasicParsing
}

Write-Host "Files in wrapper:"
Get-ChildItem wrapper

Write-Host "Building..."
& java -classpath $JarDst org.gradle.wrapper.GradleWrapperMain assembleDebug
pause
