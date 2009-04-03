# Returns 0 if arguments include a help switch (/?), or 1 otherwise.
# (C) Elias Fotinis 2007.03.03
#
# Useful for checking the presense of a help switch in BAT files, e.g.:
#
#   @ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
#   ECHO ...help...
#   GOTO :EOF
#   :skipHelp
#
import sys
hasHelp = '/?' in sys.argv[1:]
sys.exit(1 - int(hasHelp))  # return 0 if True, otherwise 1
