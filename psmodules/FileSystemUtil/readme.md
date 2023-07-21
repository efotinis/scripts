File-system Utilities
=====================

File and path related functions that access or depend on the filesystem.


Filtering
---------

Select file items whose extensions match (or do not match) broad type, such as video, image, archive, etc:

* `Get-ExtensionCategory`

Scan directories recursively, excluding certain patterns (e.g. dot-prefixed) :

* `Get-FilterDirectory`


Links
-----

Batch creation of hard/soft-links into a target directory:

* `New-HardLink`
* `New-IndexedItem`


Renaming
--------

Rename files and directories using regular expressions:

* `Rename-Pattern`
