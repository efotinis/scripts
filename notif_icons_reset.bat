:: Restarts certain programs *if* they are running.
:: This is useful for programs that fail to recreate
:: their notification icons when Explorer crashes.

@ECHO OFF & SETLOCAL ENABLEEXTENSIONS

CALL :restart "C:\WINDOWS\system32\taskmgr.exe"
CALL :restart "C:\WINDOWS\mixer.exe" "/startup"
CALL :restart "C:\Program Files\refreshlock\RefreshLock.exe"
CALL :restart "C:\Program Files\OteCount\OteCount.exe"
CALL :restart "C:\Program Files\ahead\Nero ToolKit\DriveSpeed.exe"
CALL :restart "C:\Program Files\FlatTaskbar\FlatTaskbar.exe"
CALL :restart "C:\Program Files\ScreenSwitch.exe"

GOTO :EOF



::--------------------
:: Checks whether a program is running and, if so, terminates it and restarts it.
::   %1  Program path (possibly relative) (e.g. 'C:\Windows\Notepad.exe' or 'notepad.exe')
::   %2  Additional run params (may be empty)
::--------------------
:restart

IF NOT EXIST "%~1" (
  ECHO Could not find %1.
  GOTO :EOF
)

:: check whether task is running
TASKLIST /NH /FO CSV /FI "IMAGENAME EQ %~nx1" 2> NUL | FINDSTR /L /B /I /C:"\"%~nx1\"" > NUL
IF ERRORLEVEL 1 (
  ECHO %~nx1 is not running.
  GOTO :EOF
)

:: kill task
TASKKILL /F /IM %~nx1 > NUL
IF ERRORLEVEL 1 (
  ECHO Could not kill %~nx1.
  GOTO :EOF
)

:: restart task
ECHO Restarting %~nx1.
START "" "%~1" %2
GOTO :EOF
