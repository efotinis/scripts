@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Stores the last output line from a command into an env-var.
ECHO.(C) Elias Fotinis
ECHO.
ECHO.LNSET var cmd
ECHO.
ECHO.  var  An env-var id.
ECHO.  cmd  A command string (NOTE: must be single token; use quotes if needed).
GOTO :EOF
:skipHelp

@FOR /F "delims=" %%i IN ('%~2') DO @SET %1=%%i
