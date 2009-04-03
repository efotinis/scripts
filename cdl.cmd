@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Change current directory to long-name version of itself.
ECHO.(C) Elias Fotinis 2007.03.01
ECHO.
ECHO.Useful when exiting from DOS and 16-bit apps.
GOTO :EOF
:skipHelp

FOR /F "delims=" %%A IN ('longcwd') DO CD %%A

