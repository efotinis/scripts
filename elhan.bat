@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Sets up some macros for ERRORLEVEL handling.
ECHO.(C) Elias Fotinis 2007
ECHO.
ECHO.The macros created are:
ECHO.  EL   Displays current ERRORLEVEL.
ECHO.  EL0  Sets ERRORLEVEL to 0.
ECHO.  EL1  Sets ERRORLEVEL to 1.
GOTO :EOF
:skipHelp

DOSKEY EL=ECHO %%ERRORLEVEL%%
DOSKEY EL0=TIME /T ^> NUL
DOSKEY EL1=VERIFY FOO ^> NUL 2^>^&1
