ModularPrompt
=============

A customizable console prompt, with multiple subitems and color support.

Colors are defined using the dBase extended format defined in the ColorUtil module.


Item manipulation
-----------------

A global function is exported to track and display items:

* `prompt`

Accessing individual items, each supporting a color and an expression to calculate the content:

* `Add-ModPromptItem`
* `Get-ModPromptItem`
* `Set-ModPromptItem`
* `Remove-ModPromptItem`

Set default configuration:

* `Reset-ModPrompt`

Resetting replaces all current items with the following:

1. Elevation (admin) indicator.
2. Background job counter.
3. Current path.
4. Prompt nesting level.


Options
-------

These handle settings (similiar to Get/Set-PSReadLineOption), such as default item color and display mode of the path item:

* `Get-ModPromptOption`
* `Set-ModPromptOption`
