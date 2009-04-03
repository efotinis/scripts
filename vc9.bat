@ECHO OFF
IF '%1'=='/?' (
    ECHO Setup VC9 cmdline tools.
    GOTO :EOF
)
CALL C:\DevTools\VS9\Common7\Tools\vsvars32.bat
CALL prompt_sep
TITLE VC9
SET CL=/nologo
