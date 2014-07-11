:: Convert a directory of video files to MP3.
@echo off & setlocal enableextensions enabledelayedexpansion

set ffmpeg=c:\Users\Elias\Program Files\ffmpeg-20130226-git-f6fff8e-win32-shared\bin\ffmpeg.exe

set outdir=%~1
set quality=%~2
set help=0
call :chkHelp "%outdir%"
call :chkHelp "%quality%"
call :chkHelp "%3"
if %help% == 1 goto usage
shift
shift
goto main

:chkHelp
if "%~1" == "" (set help=1 & goto :eof)
if "%~1" == "/?" (set help=1 & goto :eof)
if "%~1" == "-h" (set help=1 & goto :eof)
goto :eof

:usage
echo convert dir of videos to mp3s
echo.
echo %~nx0% DEST VBRQ INPUT [...]
echo   DEST   output directory; source filenames are used
echo   VBRQ   VBR quality; 1 (best quality) to 9 (smallest size)
echo   INPUT  input file or pattern
goto :eof

:main
if "%~1" == "" goto :eof
for %%f in ("%~1") do @(
    set src=%%f
    set dst=!outdir!\%%~nf.mp3
    "%ffmpeg%" -i "!src!" -vn -acodec libmp3lame -q:a %quality% "!dst!"
)
shift
goto :main
