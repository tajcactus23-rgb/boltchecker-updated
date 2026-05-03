@echo off
setlocal enabledelayedexpansion

REM Gradle Wrapper for Windows
set DIRNAME=%~dp0
if "%DIRNAME:~-1%"=="\" set DIRNAME=%DIRNAME:~0,-1%

set DEFAULT_JVM_OPTS=-Xmx64m
set JAVA_OPTS=%DEFAULT_JVM_OPTS% -Djava.security.manager=awt.toolit.headless=true

set CLASSPATH=

for /f "tokens=*" %%a in ('dir /b "%DIRNAME%\gradle\wrapper\gradle-wrapper.jar" 2^>nul') do set WRAPPER_JAR=%%a

if not defined WRAPPER_JAR (
    echo.
    echo ERROR: gradle-wrapper.jar not found!
    echo Download full Gradle wrapper files
    pause
    exit /b 1
)

set WRAPPER_CONF="%DIRNAME%\gradle\wrapper\gradle-wrapper.properties"

if not exist %WRAPPER_CONF% (
    echo.
    echo ERROR: gradle-wrapper.properties not found!
    pause
    exit /b 1
)

set JAVABIN=java

"%JAVABIN%" -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Java not found! Install Java 17+
    pause
    exit /b 1
)

echo Gradle is downloading. This may take a few minutes...

"%JAVABIN%" -Dgradle.wrapper.launcher.inherited=true %JAVA_OPTS% -classpath %WRAPPER_JAR% org.gradle.wrapper.GradleWrapperMain %*

echo.
echo Gradle finished
pause