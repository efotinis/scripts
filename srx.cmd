@echo off & setlocal enableextensions

set url=
set sr_exe=C:\Program Files (x86)\Streamripper\streamripper.exe

echo Station/channel to rip (Ctrl-C to exit):
echo.
echo   a  SomaFM / Lush
echo   b  000Audio / 80s Pop
echo.

choice /c ab /n /m "Select: "

if %errorlevel% equ 0 goto :eof
if %errorlevel% equ 255 goto :eof
if %errorlevel% equ 1 set url=http://205.188.214.184:8420/
if %errorlevel% equ 2 set url=http://66.103.27.16:9310/

"%sr_exe%" "%url%" -d e:\streamripper -r
