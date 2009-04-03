@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Print file extension statistics. [deprecated]
ECHO.(C) Elias Fotinis
GOTO :EOF
:skipHelp

cscript //nologo "C:\Program Files\(misc)\extstat.js" %*
