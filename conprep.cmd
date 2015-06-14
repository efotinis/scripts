:: Enhance the console.
::
:: Can be run automatically using the "Autorun" value of the 
:: "HKLM\SOFTWARE\Microsoft\Command Processor" key.
::
@echo off & setlocal enableextensions

:: clear copyright; use this instead of CLS to preserve
:: the console contents of nested CMD instances
eatlines 2

:: common shorthands
doskey /macrofile=d:\scripts\common.mac

:: switch to ANSI codepage
chcp 1253 >nul

:: change colors if console is elevated; "FSUTIL.exe" is used to detect 
:: elevation (by setting ERROLEVEL) and "time /t" resets the ERRORLEVEL
%windir%\system32\FSUTIL.exe >nul 2>&1 && color 4f & time /t >nul

:: note that ERRORLEVEL should always be reset on exit from here,
:: since this is a startup script
