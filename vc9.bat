@ECHO OFF
IF '%1'=='/?' (
    ECHO Setup VC9 cmdline tools.
    GOTO :EOF
)
CALL "%VS90COMNTOOLS%\vsvars32.bat"
CALL prompt_sep
TITLE VC9
SET CL=/nologo
