@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Display help of all scripts.
ECHO.(C) Elias Fotinis
GOTO :EOF
:skipHelp

::PY is not needed, BUT:
::we MUST use it to work around a Windows bug with std handles
FOR %%F IN (*.BAT) DO (
  clrPrint "{i}---- %%F ----{r}"
  %%F /? | PY lineFilter.py /N 0
  ECHO.
)
