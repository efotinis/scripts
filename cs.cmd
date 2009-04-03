@ECHO OFF & SETLOCAL ENABLEEXTENSIONS
:: Runs a script with CSCRIPT //NOLOGO.
:: (C) Elias Fotinis

IF '%1' == '' (
  ECHO.No script specified.
  GOTO :EOF
)

CSCRIPT //NOLOGO %*
