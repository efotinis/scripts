:: make thumbnails of all specified items (video files or dirs)
@echo off & setlocal enableextensions
set mtn=C:\prg\movie thumbnailer\mtn.exe
"%mtn%" -P -j70 -h50 -c6 -r5 -w1280 -o.jpg %*