REM Creates an html album, i.e. an INDEX.HTML file consisting of two frames.
REM The left frame is a list of filenames, which the user can click to display
REM their contents in the right frame.
REM The files must be in the same directory as the INDEX.HTML file.
REM 
REM Usage:  HTMLIST.BAT mask
REM   where 'mask' is the files to include in the album.
REM   It can be a single mask (e.g. *.jpg)
REM   or multiple ones separated by spaces and delimited in double quotes
REM   (e.g. "*.jpg *.png *.tif")
REM
REM Note if either of the output files (INDEX.HTML, CONTENTS.HTML) exist
REM it will be overwritten.
REM
REM Created by Elias Fotinis
REM 2003 - released to the public domain
REM
REM
REM NOTE: This was a nice little batch, but I really have to
REM       convert this to a GUI app, drag 'n drop, and stuff....
REM

@ECHO OFF

REM -- frames page
ECHO ^<html^>                                        >  index.html
ECHO ^<frameset cols="150,*"^>                       >> index.html
ECHO   ^<frame name="contents" src="contents.html"^> >> index.html
ECHO   ^<frame name="main" src=""^>                  >> index.html
ECHO ^</frameset^>                                   >> index.html
ECHO ^</html^>                                       >> index.html

REM -- contents page
ECHO ^<html^>^<head^>^<style^>                                           >  contents.html
ECHO a { text-decoration: none; }                                        >> contents.html
ECHO a:hover { text-decoration: underline; }                             >> contents.html
ECHO ^</style^>^</head^>^<body^>                                         >> contents.html
FOR %%1 IN (%~1) DO ECHO ^<a href='%%1' target='main'^>%%~n1^</a^>^<br^> >> contents.html
ECHO ^</body^>^</html^>                                                  >> contents.html
