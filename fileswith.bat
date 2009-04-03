@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.??? :)
ECHO.(C) Elias Fotinis
GOTO :EOF
:skipHelp

CSCRIPT /NOLOGO "C:\Program Files\(misc)\fileswith.js" %*
GOTO :EOF



@ECHO OFF & SETLOCAL ENABLEEXTENSIONS

IF "%1" == ""   GOTO help
IF "%1" == "/?" GOTO help

CALL :getSwitch %1 switch
ECHO Switch: %switch%
GOTO :EOF


SET foo=%~1
SET foo=%foo%%foo%
ECHO %foo%
GOTO :EOF



::----------------------------------
:getSwitch
:: %1  argument
:: %2  name of var to set
::----------------------------------
SET tmp=%1
IF %tmp:~0,1% == / (
  SET %2=%tmp:~1%
) ELSE (
  SET %2=
)
GOTO :EOF

::----------------------------------
:help
::----------------------------------
ECHO.List files either containing or not a string.
ECHO.
ECHO.%0 [/C] [/N] "string" files[ ...]
ECHO.
ECHO.  /C    Match case of string. By default, case is ignored.
ECHO.  /N    Show files that do not contain the specified string.
ECHO.  text  The text string to find.
ECHO.  file  One or more files (wildcards allowed) to search.
GOTO :EOF



for %f in (*.hpp) do @(find /i "_MSC_VER >= 1020" %f > nul && echo %f)
