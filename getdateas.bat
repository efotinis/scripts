@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Executes GetDate.exe and stores its output in an environment variable.
ECHO.(C) Elias Fotinis
ECHO.
ECHO.GETDATEAS env params
ECHO.
ECHO.  env     The name of the environment variable.
ECHO.  params  The GetDate.exe params.
GOTO :EOF
:skipHelp

SET gdaVarName=%1
SET gdaTmpFile=%TEMP%\~getdateas.$$$
IF "%gdaVarName%" == "" ECHO %0: Missing variable name & GOTO :EOF

:: get rid of the envVar name
SHIFT

d:\Projects\console\getdate\Release\getdate.exe %1 %2 %3 %4 %5 %6 %7 %8 %9 > %gdaTmpFile%
IF ERRORLEVEL 1 (
	ECHO %0: getdate.exe failed
	SET %gdaVarName%=
) ELSE (
	SET /P %gdaVarName%=<%gdaTmpFile%
)

DEL %gdaTmpFile% > NUL
SET gdaTmpFile=
SET gdaVarName=
GOTO :EOF
