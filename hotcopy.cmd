@ECHO OFF & SETLOCAL ENABLEEXTENSIONS

IF "%1" == "" GOTO help
IF "%1" == "/?" GOTO help

SET HOBO="C:\Program Files\HoboCopy\HoboCopy.exe"
SET SRCDIR=%~1
SET DSTDIR=%~2
SET SRCNAME=%~3
SET DSTNAME=%~4

%HOBO% "%SRCDIR%" "%DSTDIR%" "%SRCNAME%"
IF NOT "%DSTNAME%" == "" (
    REN "%DSTDIR%\%SRCNAME%" "%DSTNAME%"
)
GOTO :EOF

:help
ECHO Copy a locked file using HOBOCOPY.
ECHO Usage: GRABIT srcDir dstDir srcName [dstName]
