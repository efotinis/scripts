@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Sets console size.
ECHO.(C) Elias Fotinis
ECHO.
ECHO.RC rows cols
ECHO.
ECHO.  rows  The number of rows (25, 43 or 50).
ECHO.  cols  The number of cols (40 or 80).
GOTO :EOF
:skipHelp

MODE CON LINES=%1 COLS=%2
