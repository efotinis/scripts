@ECHO OFF & SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

SET lockFile=%TEMP%\ati_error.lock
IF EXIST %lockFile% GOTO :EOF

ECHO.>%lockFile%

COLOR 4f

ECHO.Running tasks
ECHO.============
FOR /F "delims=" %%s IN ('tasklist /fo list ^| find "Image Name:" ^| sort') DO @(
    SET taskLine=%%s
    ECHO !taskLine:~14!
)
ECHO.

ECHO.%DATE% %TIME%
ECHO.

ECHO.An ATI related event has been logged.
ECHO.Check the Event Log.
ECHO.

PAUSE

DEL %lockFile%
