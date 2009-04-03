@ECHO OFF
IF '%1'=='/?' (
    ECHO Setup VC7.1 cmdline tools.
    GOTO :EOF
)
CALL D:\dev\VS7.1\Common7\Tools\vsvars32.bat
CALL prompt_sep
TITLE VC71
SET CL=/nologo
