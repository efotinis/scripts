@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Print file extension statistics. [deprecated]
ECHO.(C) Elias Fotinis
GOTO :EOF
:skipHelp

::(FOR /F "delims=" %%A IN ('DIR "%~1" /S /A-D /B') DO @ECHO.%%~xA) | SORT | TXTOPS GRP /U /DF /N /I | SORT /R

DIR "%~1" /S /A-D /B | cscript /nologo "c:\program files\(misc)\file_ext_filter.js" | SORT | TXTOPS GRP /U /DF /N /I | SORT
