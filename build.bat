@echo off
chcp 65001 >nul
title BOLTFM Build
echo.

REM Create folders
if not exist "gradle\wrapper" mkdir "gradle\wrapper"
if not exist "app\src\main\assets" mkdir "app\src\main\assets"

REM Get Gradle if missing
if not exist "gradle\wrapper\gradle-wrapper.jar" (
    echo Downloading Gradle Wrapper...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/tajcactus23-rgb/boltchecker-updated/main/gradle/wrapper/gradle-wrapper.jar' -OutFile 'gradle\wrapper\gradle-wrapper.jar'"
)

REM Build
java -classpath "gradle\wrapper\gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain assembleDebug

pause