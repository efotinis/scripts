@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Sets an env var to the n-th line of a command's output.
ECHO.(C) Elias Fotinis 2006
ECHO.
ECHO.VSET var cmd [line]
ECHO.
ECHO.  var   The variable name to create.
ECHO.  cmd   The command whose output to capture.
ECHO.  line  The line number to use; default is 1.
GOTO :EOF
:skipHelp


REM :: (See help label below)
REM :: We can't use 'cmd | SET /P var='; SET just does nothing...
REM :: Anyway, using a temp file allows us to get any line,
REM :: not just the first.


ENDLOCAL


::::::::SET _TMPFILE=%TEMP%\~VSET.$$$
::::::::SET _TMPFILE2=%TEMP%\~VSET2.$$$
SET _TMPFILE=~VSET.$$$
SET _TMPFILE2=~VSET2.$$$
%~2 > %_TMPFILE%

SET _LINENO=%3
IF '%_LINENO%' == '' SET _LINENO=1

lnfilt %_TMPFILE% %_LINENO% > %_TMPFILE2%
IF ERRORLEVEL 1 (
  ECHO ERROR: VSET.BAT: LNFILT failed
  GOTO :EOF
)
SET /P %1=<%_TMPFILE2%

::::::::DEL %_TMPFILE% > NUL
::::::::DEL %_TMPFILE2% > NUL
DEL %_TMPFILE% > NUL
DEL %_TMPFILE2% > NUL
SET _TMPFILE=
SET _TMPFILE2=
