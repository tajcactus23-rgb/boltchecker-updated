Set-Location $PSScriptRoot
$b = $PSScriptRoot
Write-Host "Base: $b"
Write-Host "Contents:"
Get-ChildItem $b | Select Name

# Download directly
$jar = "$b\gw.jar"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.jar" -OutFile $jar -UseBasicParsing
Write-Host "Got: $(Get-Item $jar).Length"
Write-Host "Running..."
java -classpath $jar org.gradle.wrapper.GradleWrapperMain assembleDebug
pause
