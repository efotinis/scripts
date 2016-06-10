:: make thumbnails of all specified items (video files or dirs)
@echo off & setlocal enableextensions
set mtn=C:\prg\movie thumbnailer\mtn.exe
:: NOTE: the min height flag (-h50) causes some thumbs to fail; since the
:: affected videos are usually short, omitting all of -h -c -r will produce
:: an acceptable output (unfortunately, this must be done manually)
"%mtn%" -P -j70 -h50 -c6 -r5 -w1280 -o.jpg %*
