@echo off
chcp 65001 >nul
title BOLTFM Build
echo.

REM Create folders
if not exist "gradle" mkdir "gradle"
if not exist "gradle\wrapper" mkdir "gradle\wrapper"
if not exist "app" mkdir "app"
if not exist "app\src" mkdir "app\src"
if not exist "app\src\main" mkdir "app\src\main"
if not exist "app\src\main\assets" mkdir "app\src\main\assets"

REM Get Gradle wrapper files
if not exist "gradle\wrapper\gradle-wrapper.jar" (
    echo Downloading Gradle Wrapper...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.jar' -OutFile 'gradle\wrapper\gradle-wrapper.jar'"
)

if not exist "gradle\wrapper\gradle-wrapper.properties" (
    echo Downloading Gradle properties...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.properties' -OutFile 'gradle\wrapper\gradle-wrapper.properties'"
)

REM Build
java -classpath "gradle\wrapper\gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain assembleDebug
pause
