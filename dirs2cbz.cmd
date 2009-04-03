@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Creates (uncompressed) CBZs from the files of all subdirs of current dir.
ECHO.(C) Elias Fotinis
GOTO :EOF
:skipHelp

FOR /D %d IN (*) DO @PUSHD "%d" & 7z a "..\%d" * -tzip -mx=0 & POPD
