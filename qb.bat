@ECHO OFF & SETLOCAL ENABLEEXTENSIONS
:: QB.EXE wrapper.
:: (C) Elias Fotinis
::
:: QB needs its INI in the current(!) dir.
:: Create a hardlink and delete on exit.
::
:: Previously, a hardlink to QB45\QB.INI was created in the cur dir
:: and deleted on exit. However, hardlinks are only available for files
:: in the same drive.
::
:: This version uses this aproach:
:: - If QB.INI exists, do nothing.
:: - Copy QB.INI to cur dir and clear archive flag.
:: - If copying failed (e.g. cur dir is on a read-only drive), do nothing.
:: - When QB exits test the archive flag of the local QB.INI.
:: - IF the above is set, copy it to QB45\QB.INI
::

SET qb_dir=%ProgramFiles%\QB45
SET qb_manage_ini=1

IF EXIST QB.INI (
  SET qb_manage_ini=0
  GOTO run
)

COPY /B "%qb_dir%\QB.INI" QB.INI > NUL 2>&1
IF ERRORLEVEL 1 (
  SET qb_manage_ini=0
  GOTO run
)

ATTRIB -A QB.INI

:run
CHCP 737 > NUL
"C:\Program Files\QB45\qb.exe" %*
CHCP 1253 > NUL

IF %qb_manage_ini% == 1 (
  XCOPY /A /Y QB.INI "%qb_dir%\QB.INI" > NUL 2>&1
  DEL QB.INI > NUL 2>&1
)

:: Restore cur dir to long format
CALL CDL
