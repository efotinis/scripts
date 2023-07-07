Date Utilities
==============

Date/time related functions.


Date string conversions
-----------------------

Convert to/from 'yyyyMMdd' strings.

* `ConvertTo-CompactDate`
* `ConvertFrom-CompactDate`

Convert from US-style date ('M.d.[yy]yy' and 'M/d/[yy]yy').

* `ConvertFrom-USDate`


Date sections
-------------

Work with date sections, i.e. strings representing year ('yyyy'), quarter ('yyyy-Qn') or month ('yyyy-MM') of a date.

Convert to/from section string or get its type:

* `ConvertTo-DateSection`
* `ConvertFrom-DateSection`
* `Get-DateSectionType`

Get the next/previous section or whole range between two sections:

* `Get-NextDateSection`
* `Get-PreviousDateSection`
* `Get-DateSectionRange`

Group objects based on date section:

* `Group-DateSection`


Date/time offsets
-----------------

Modify current datetime.

Add multiple date or time parts:

* `Get-DateAgo`
* `Get-TimeAgo`

Get the next/previous instance of the time of the day:

* `Get-NextTime`
* `Get-PreviousTime`
