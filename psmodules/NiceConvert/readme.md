Human-Readable Values
=====================

Convert values to string that are easier to understand.


Time
----

Convert seconds to/from strings in the form of `'[h:]mm:ss'`:

* `ConvertFrom-NiceDuration`
* `ConvertTo-NiceDuration`

Convert seconds to `'hh:mm:ss'`:

* `ConvertTo-NiceSeconds`

Convert DateTime/TimeSpan to variable precision string denoting years, months, days, hours, etc.:

* `ConvertTo-NiceAge`


Bytes
-----

Convert to/from approximate size representations with unit and 3 significant digits. Supports decimal, JEDEC and binary formats:

* `ConvertFrom-NiceSize`
* `ConvertTo-NiceSize`
