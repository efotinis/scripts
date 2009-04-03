@ECHO OFF & SETLOCAL ENABLEEXTENSIONS
:: Runs EDIT.COM with an OEM codepage and then restores the ANSI codepage.
:: ECHO.(C) Elias Fotinis 2007

CHCP 737 > NUL
"%SystemRoot%\SYSTEM32\edit.COM" %*
CHCP 1253 > NUL
:: Restore cur dir to long format
CALL CDL
