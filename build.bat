@echo off
chcp 65001 >nul
title BOLTFM Build
cd /d %~dp0
mkdir gradle 2>nul
mkdir gradle\wrapper 2>nul
mkdir app 2>nul
mkdir app\src 2>nul
mkdir app\src\main 2>nul
mkdir app\src\main\assets 2>nul
dir gradle\wrapper
pause
