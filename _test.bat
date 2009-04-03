@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Help
GOTO :EOF
:skipHelp
ECHO.No help
