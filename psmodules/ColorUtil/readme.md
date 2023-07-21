Color Utilities
===============

Functions to convert various console color formats to dBase/Clipper-style specs. These are, in my opinion, much easier to interact with, especially when compared to raw ANSI sequences.

The original format is a string like 'FG/BG' where each color can be one of:

* `'n'` / `'n+'`: black       / darkgray
* `'b'` / `'b+'`: darkblue    / blue
* `'g'` / `'g+'`: darkgreen   / green
* `'c'` / `'c+'`: darkcyan    / cyan
* `'r'` / `'r+'`: darkred     / red
* `'m'` / `'m+'`: darkmagenta / magenta
* `'y'` / `'y+'`: darkyellow  / yellow
* `'w'` / `'w+'`: gray        / white

I've extended the above to include the following:

* indexed colors: `'#<NUM>'`, where NUM is 0..255
* true colors: `'<R>,<G>,<B>'`, where R,G,B are 0..255
* effects represented as characters: `'<FG>/<BG>/<EFFECTS>'`


PowerShell console
------------------

Convert to/from a pair of `[System.ConsoleColor]`:

* `ConvertFrom-ConsoleColor`
* `ConvertTo-ConsoleColor`


ANSI escape sequences
---------------------

Convert to/from strings in the form of `"$([char]27)[...m"`:

* `ConvertFrom-AnsiColor`
* `ConvertTo-AnsiColor`
