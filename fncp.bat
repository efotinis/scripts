@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.??? :)
ECHO.(C) Elias Fotinis
GOTO :EOF
:skipHelp

"E:\Projects\console\fncp\Release\fncp.exe" %*
