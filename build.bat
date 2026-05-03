@echo off
chcp 65001 >nul
color 0a
title BOLTFM Build
echo.
echo ========================================
echo       BOLTFM Android Builder
echo ========================================
echo.

REM Check for Java
java -version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Java not found!
    echo Install Java 17 first: https://adoptium.net/
    pause
    exit
)

REM Check for SDK
if not exist "local.properties" (
    echo Setting SDK path...
    echo sdk.dir=C:\platformtools > local.properties
)

REM Create assets folder
if not exist "app\src\main\assets" mkdir "app\src\main\assets"

REM Copy HTML
echo Copying index.html...
copy /Y index.html app\src\main\assets\ >nul

REM Build
echo Building APK...
call gradlew.bat assembleDebug --no-daemon

echo.
echo ========================================
if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo SUCCESS!
    echo APK: app\build\outputs\apk\debug\app-debug.apk
) else (
    echo FAILED - Check errors above
)
echo ========================================
pause