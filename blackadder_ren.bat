@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Rename Black Adder video files to include episode titles.
ECHO.(C) Elias Fotinis 2005.05.27
ECHO.
ECHO.BLACKADDER_REN dir
ECHO.
ECHO.  dir  The dir path containing the files.
GOTO :EOF
:skipHelp

CALL :rename "%~1" "2.1" "2.2 - Head"
CALL :rename "%~1" "2.2" "2.1 - Bells"
CALL :rename "%~1" "2.3" "2.3 - Potato"
CALL :rename "%~1" "2.4" "2.4 - Money"
CALL :rename "%~1" "2.5" "2.5 - Beer"
CALL :rename "%~1" "2.6" "2.6 - Chains"
CALL :rename "%~1" "3.1" "3.1 - Dish and Dishonesty"
CALL :rename "%~1" "3.2" "3.2 - Ink and Incapability"
CALL :rename "%~1" "3.3" "3.3 - Nob and Nobility"
CALL :rename "%~1" "3.4" "3.4 - Sense and Senility"
CALL :rename "%~1" "3.5" "3.5 - Amy and Amiability"
CALL :rename "%~1" "3.6" "3.6 - Duel and Duality"
GOTO :EOF

:rename
::  %1  dir path
::  %2  season/episode (e.g. "3.5")
::  %3  correct season/episode & title (e.g. "3.5 - Title")
REN "%~1\Black adder %~2.avi" "Blackadder %~3.avi" 
GOTO :EOF
