@echo off
echo Building BOLTFM Android App...

REM Check for local.properties
if not exist "local.properties" (
    echo Creating local.properties...
    (
        echo sdk.dir=C:\Android\Sdk
    ) > local.properties
)

REM Copy index.html to assets
if exist "index.html" (
    echo Copying index.html to assets...
    if not exist "app\src\main\assets" mkdir "app\src\main\assets"
    copy /Y index.html app\src\main\assets\
)

REM Build APK
echo Building APK...
gradlew.bat assembleDebug

if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo.
    echo SUCCESS! APK at: app\build\outputs\apk\debug\app-debug.apk
) else (
    echo.
    echo Build failed. Check errors above.
)

pause