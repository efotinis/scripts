@echo off & setlocal enableextensions

set url=
set sr_exe=C:\Program Files (x86)\Streamripper\streamripper.exe
set out_dir=D:\streamripper

echo Station/channel to rip (Ctrl-C to exit):
echo.
echo   a  SomaFM / Lush
echo   b  SomaFM / Underground Eighties
echo   c  SomaFM / Drone Zone
echo   d  000Audio / 80s Pop
echo   e  Swiss Jazz Radio

echo.

choice /c abcd /n /m "Select: "

if %errorlevel% equ 0 goto :eof
if %errorlevel% equ 255 goto :eof
if %errorlevel% equ 1 set url=http://205.188.214.184:8420/
if %errorlevel% equ 2 set url=http://ice.somafm.com/u80s
if %errorlevel% equ 3 set url=http://streamer-dtc-aa04.somafm.com/stream/1032
if %errorlevel% equ 4 set url=http://66.103.27.16:9310/
if %errorlevel% equ 5 set url=http://glb-stream15.streamserver.ch/1/rsj/aacp_64

"%sr_exe%" "%url%" -d "%out_dir%" -r -q
