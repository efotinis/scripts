<#
.SYNOPSIS
    Convert 'yyyyMMdd' to datetime.

.DESCRIPTION
    Converts a compact date string in the format 'yyyyMMdd' to a DateTime object.

    The time part of the output date is set to midnight.

.PARAMETER Date
    Input date string. Can pass multiple values via the pipeline.

.INPUTS
    string

.OUTPUTS
    datetime

.EXAMPLE
    PS> '19780227' | ConvertFrom-CompactDate  # my dirthdate
    Monday, February 27, 1978 00:00:00
#>
function ConvertFrom-CompactDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Date
    )
    process {
        [datetime]::new(
            [int]$Date.Substring(0, 4),
            [int]$Date.Substring(4, 2),
            [int]$Date.Substring(6, 2)
        )
    }
}


<#
.SYNOPSIS
    Convert datetime to 'yyyyMMdd'.

.DESCRIPTION
    Converts a DateTime object to a compact date string in the format 'yyyyMMdd'.

    The time part of the input date is ignored.

.PARAMETER Date
    Input datetime object. Can pass multiple values via the pipeline.

.INPUTS
    datetime

.OUTPUTS
    string

.EXAMPLE
    PS> Get-Date | ConvertTo-CompactDate
    20230705
#>
function ConvertTo-CompactDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [datetime]$Date
    )
    process {
        $Date.ToString('yyyyMMdd')
    }
}


<#
.SYNOPSIS
    Convert US-style date to datetime.

.DESCRIPTION
    Converts a string of a US-style date to a datetime object. The following formats are recognized:
        - M/d/yy
        - M/d/yyyy
        - M.d.yy
        - M.d.yyyy
    Years with 2 digits are assumed to be in the 2000s.

.PARAMETER Date
    Input date string. Can pass multiple values via the pipeline.

.PARAMETER Scan
      Search for any matching substring within input.

.INPUTS
    string

.OUTPUTS
    datetime

.EXAMPLE
    PS> ConvertFrom-USDate 7.4.1776
    Thursday, July 4, 1776 00:00:00

.EXAMPLE
    PS> '12/25/23' | ConvertFrom-USDate
    Sunday, December 25, 2023 00:00:00
#>
function ConvertFrom-USDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Date,

        [switch]$Scan
    )
    begin {
        $s1 = '(\d{1,2})/(\d{1,2})/(\d{2,4})'
        $s2 = '(\d{1,2})\.(\d{1,2})\.(\d{2,4})'
        $rx = [regex]$(if ($Scan) {
            "$s1|$s2"
        } else {
            "^$s1$|^$s2$"
        })
    }
    process {
        $a = $rx.Match($Date)
        if (-not $a.Success) {
            Write-Error "No US-style date found in string: $Date"
            return
        }
        if ($a.Groups[1].Value) {
            $m, $d, $y = $a.Groups[1..3].Value
        } else {
            $m, $d, $y = $a.Groups[4..6].Value
        }
        $y, $m, $d = @($y, $m, $d).ForEach([int])
        if ($y -lt 100) {
            $y += 2000
        }
        [datetime]::new($y, $m, $d)
    }
}


<#
.SYNOPSIS
    Convert datetime to string denoting year, quarter or month.

.DESCRIPTION
    Converts a datetime to a coarser date section (year, quarter or month) string.

    See Type parameter for output string formats.

.PARAMETER Date
    Input datetime. Can pass multiple values via the pipeline.

.PARAMETER Type
    Output date section type. Possible values with output formats:
        - Year      'yyyy'
        - Quarter   'yyyy-Qn', where n is 1..4
        - Month     'yyyy-MM'

.INPUTS
    datetime

.OUTPUTS
    string

.EXAMPLE
    PS> Get-Date | ConvertTo-DateSection -Type Quarter
    2023-Q3

    Given a current date of July 5, 2023, the above returns the 3rd quarter of 2023.

.EXAMPLE
    PS> ConvertTo-DateSection -Date '2000-12-25' -Type Month
    2000-12

    Here the Christmas date of 2000 is converted to year and month.
#>
function ConvertTo-DateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [datetime]$Date,

        [Parameter(Mandatory, Position = 0)]
        [ValidateSet('Year', 'Quarter', 'Month')]
        [string]$Type
    )
    process {
        switch ($Type) {
            'Year' {
                $Date.ToString('yyyy')
            }
            'Quarter' {
                $y = $Date.Year
                $m = $Date.Month
                $q = [int]([System.Math]::Truncate(($m - 1) / 3) + 1)
                '{0:D4}-Q{1}' -f $y,$q
            }
            'Month' {
                $Date.ToString('yyyy-MM')
            }
            default {
                Write-Error "Unexpected date section type: $Type."
            }
        }
    }
}


<#
.SYNOPSIS
    Convert string denoting year, quarter or month to datetime.

.DESCRIPTION
    Converts a string of a coarse date section (year, quarter or month) to a datetime object.

    The type of the date section is automatically detected with default components as follows:
        - 'yyyy'    January 1st of year
        - 'yyyy-Qn' January, April, July or October 1st of year.
        - 'yyyy-MM' Month 1st of year.

.PARAMETER Section
    Input date section. Can specify multiple values via the pipeline.

.INPUTS
    string

.OUTPUTS
    datetime

.EXAMPLE
    PS> ConvertFrom-DateSection '2023-q3'
    Saturday, July 1, 2023 00:00:00
#>
function ConvertFrom-DateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                $y = [int]$Matches[1]
                [datetime]::new($y, 1, 1)
            }
            '^(\d\d\d\d)-Q(\d)$' {
                $y = [int]$Matches[1]
                $q = [int]$Matches[2]
                $m = ($q - 1) * 3 + 1
                [datetime]::new($y, $m, 1)
            }
            '^(\d\d\d\d)-(\d\d)$' {
                $y = [int]$Matches[1]
                $m = [int]$Matches[2]
                [datetime]::new($y, $m, 1)
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


<#
.SYNOPSIS
    Convert to next date section.

.DESCRIPTION
    Converts a date section (year, quarter or month) to the corresponding next section.

.PARAMETER Section
    Input date section. Can specify multiple values via the pipeline.

    Supported formats and result:
        - Year      'yyyy', returns next year
        - Quarter   'yyyy-Qn', where n is 1..4, returns next quarter
        - Month     'yyyy-MM', returns next month

.INPUTS
    string

.OUTPUTS
    string

.EXAMPLE
    PS> Get-NextDateSection '2023-Q4'
    2024-Q1

    Given the 4th quarter of a year returns the 1st quarter of the next year.
#>
function Get-NextDateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                $y = [int]$Matches[1]
                ++$y
                '{0:D4}' -f $y
            }
            '^(\d\d\d\d)-Q(\d)$' {
                $y = [int]$Matches[1]
                $q = [int]$Matches[2]
                if (++$q -gt 4) {
                    $q = 1
                    ++$y
                }
                '{0:D4}-Q{1}' -f $y,$q
            }
            '^(\d\d\d\d)-(\d\d)$' {
                $y = [int]$Matches[1]
                $m = [int]$Matches[2]
                if (++$m -gt 12) {
                    $m = 1
                    ++$y
                }
                '{0:D4}-{1:D2}' -f $y,$m
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


<#
.SYNOPSIS
    Convert to previous date section.

.DESCRIPTION
    Converts a date section (year, quarter or month) to the corresponding previous section.

.PARAMETER Section
    Input date section. Can specify multiple values via the pipeline.

    Supported formats and result:
        - Year      'yyyy', returns previous year
        - Quarter   'yyyy-Qn', where n is 1..4, returns previous quarter
        - Month     'yyyy-MM', returns previous month

.INPUTS
    string

.OUTPUTS
    string

.EXAMPLE
    PS> Get-PreviousDateSection '2024-Q1'
    2023-Q4

    Given the 1st quarter of a year returns the 4th quarter of the previous year.
#>
function Get-PreviousDateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                $y = [int]$Matches[1]
                --$y
                '{0:D4}' -f $y
            }
            '^(\d\d\d\d)-Q(\d)$' {
                $y = [int]$Matches[1]
                $q = [int]$Matches[2]
                if (--$q -lt 1) {
                    $q = 4
                    --$y
                }
                '{0:D4}-Q{1}' -f $y,$q
            }
            '^(\d\d\d\d)-(\d\d)$' {
                $y = [int]$Matches[1]
                $m = [int]$Matches[2]
                if (--$m -lt 1) {
                    $m = 12
                    --$y
                }
                '{0:D4}-{1:D2}' -f $y,$m
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


<#
.SYNOPSIS
    Get type of date section.

.DESCRIPTION
    Determines whether a date section string corresponds to a year, quarter or month.

.PARAMETER Section
    Input date section string. Can specify multiple values via the pipeline.

.INPUTS
    string

.OUTPUTS
    string

.EXAMPLE
    PS> Get-DateSectionType 2023-q3
    Quarter
#>
function Get-DateSectionType {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                'Year'
            }
            '^(\d\d\d\d)-Q(\d)$' {
                'Quarter'
            }
            '^(\d\d\d\d)-(\d\d)$' {
                'Month'
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


<#
.SYNOPSIS
    Get date sections in specified range.

.DESCRIPTION
    Given a starting and ending date section, this function generates all sections within that range, including the start and end.

    Note that the sections must be of the same type, i.e. year, quarter or month.

    If the starting section is greater than than the ending, the output sections are in reverse calendar order.

.PARAMETER From
    Starting date section.

.PARAMETER To
    Ending date section.

.INPUTS
    None

.OUTPUTS
    string

.EXAMPLE
    PS> Get-DateSectionRange '2023-Q3' '2024-Q2'
    2023-Q3
    2023-Q4
    2024-Q1
    2024-Q2

    The above example demonstrates specifying two quarters in different years.

.EXAMPLE
    PS> (Get-DateSectionRange '2023-06' '2023-01') -join ', '
    2023-06, 2023-05, 2023-04, 2023-03, 2023-02, 2023-01

    The above concatenates of the first six months of 2023 in reverse order.
#>
function Get-DateSectionRange {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$From,

        [Parameter(Mandatory)]
        [string]$To
    )
    $t1 = Get-DateSectionType $From
    if (-not $t1) {
        return
    }
    $t2 = Get-DateSectionType $To
    if (-not $t2) {
        return
    }
    if ($t1 -ne $t2) {
        Write-Error "Range sections have different types: $t1, $t2."
        return
    }
    if ($From -le $To) {
        do {
            Write-Output $From
            $From = Get-NextDateSection $From
        } while ($From -le $To)
    } else {
        do {
            Write-Output $From
            $From = Get-PreviousDateSection $From
        } while ($From -ge $To)
    }
}


<#
.SYNOPSIS
    Group by date section.

.DESCRIPTION
    Group objects by year, quarter or year/month. The date property can be
    specified by name or calculated using a scriptblock.

    By default, groups of all date sections between the minimum and maximum
    are generated in sorted order unless NoEmpty is set.

.PARAMETER InputObject
    Input objects. Must be passed via the pipeline.

.PARAMETER Section
    Date section to group objects by. Also determines the format of the Section
    output property. One of:

        - Year:     Example: "2023"
        - Quarter:  Example: "2023-Q1", "2023-Q4"
        - Month:    Example: "2023-01", "2023-12"

.PARAMETER Property
    The property to use as the date of the input objects. Its type can vary:

        - [string]:         Property name.
        - [scriptblock]:    Use to calculate date value. The input object is
                            made available inside the scriptblock as $_.
        - $null / omitted:  Assume input objects are DateTime objects.

.PARAMETER NoElement
    Do not include the input objects in the output as a Group property.

.PARAMETER NoEmpty
    Do not generate empty groups for date sections with no items. This also
    prevents the output from being automatically sorted by date section.

.INPUTS
    Objects.

.OUTPUTS
    Custom objects.
#>
function Group-DateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [object]$InputObject,

        [Parameter(Mandatory, Position = 0)]
        [ValidateSet('Year', 'Quarter', 'Month')]
        [string]$Section,

        [Parameter(Position = 1)]
        $Property,  # $null, string, or scriptblock

        [switch]$NoElement,

        [switch]$NoEmpty
    )
    begin {
        function MinMax ([object[]]$Value) {
            $m = $Value | measure -min -max
            $m.Minimum, $m.Maximum
        }
        if ($Property -is [scriptblock]) {
            function GetDateValue ($Obj) {
                $Property.InvokeWithContext(
                    $null,
                    [psvariable]::new('_', $Obj),
                    $null
                )[0]
            }
        } elseif ($Property -is [string]) {
            function GetDateValue ($Obj) { $Obj.$Property }
        } else {
            function GetDateValue ($Obj) { $Obj }
        }
        $groups = @{}
        function GetGroup ([string]$Key) {
            if (-not $groups.ContainsKey($Key)) {
                $groups[$Key] = @{
                    count = 0
                    items = [System.Collections.ArrayList]::new()
                }
            }
            return $groups[$Key]
        }
        function Output ([string]$Key, $Group) {
            $o = [PSCustomObject]@{
                Section = $Key
                Count = $Group.count
            }
            if (-not $NoElement) {
                Add-Member -InputObject $o Group $Group.items
            }
            Write-Output $o
        }
    }
    process {
        $k = (GetDateValue $InputObject) | ConvertTo-DateSection -Type $Section
        $g = GetGroup $k
        $g.count += 1
        if (-not $NoElement) {
            [void]$g.items.Add($InputObject)
        }
    }
    end {
        if ($NoEmpty) {
            foreach ($e in $groups.GetEnumerator()) {
                Output $e.Key $e.Value
            }
        } else {
            $keys = @($groups.Keys)
            $min, $max = MinMax $keys
            Get-DateSectionRange $min $max | % {
                Output $_ (GetGroup $_)
            }
        }
    }
}


<#
.SYNOPSIS
    Get a past time using time parts.

.DESCRIPTION
    Returns the current datetime some hours, minutes and seconds in the past. Any part can be negative to get a future time.

.PARAMETER Hours
    Number of hours.

.PARAMETER Minutes
    Number of minutes.

.PARAMETER Seconds
    Number of seconds.

.INPUTS
    None

.OUTPUTS
    DateTime
#>
function Get-TimeAgo {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [int]$Hours,

        [Parameter(Position = 1)]
        [int]$Minutes,

        [Parameter(Position = 2)]
        [int]$Seconds
    )
    (Get-Date) - [timespan]::new($Hours, $Minutes, $Seconds)
}


<#
.SYNOPSIS
    Get a past time using date parts.

.DESCRIPTION
    Returns the current datetime some years, months, days and weeks in the past. Any part can be negative to get a future time.

.PARAMETER Years
    Number of years.

.PARAMETER Months
    Number of months.

.PARAMETER Days
    Number of days.

.PARAMETER Weeks
    Number of weeks.

.INPUTS
    None

.OUTPUTS
    DateTime
#>
function Get-DateAgo {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [int]$Years,

        [Parameter(Position = 1)]
        [int]$Months,

        [Parameter(Position = 2)]
        [int]$Days,

        [Parameter()]
        [int]$Weeks
    )
    $d = Get-Date
    $Days += $Weeks * 7
    $d.AddYears(-$Years).AddMonths(-$Months).AddDays(-$Days)
}


<#
.SYNOPSIS
    Get the next occurence of a specified time.

.DESCRIPTION
    Returns the next point of time from now that has the specified time parts.

.PARAMETER TimeOfDay
    A TimeSpan object specifying the time parts. The Days member is ignored.

    Note that a string in the form of "hh:mm[:ss[.ff]]" can also be used. For more details, see the Remarks section at <https://learn.microsoft.com/en-us/dotnet/api/system.timespan.parse>.

.INPUTS
    None

.OUTPUTS
    DateTime
#>
function Get-NextTime {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        [timespan]$TimeOfDay
    )
    $TimeOfDay = [timespan]::new(
        0,  # ignore Days
        $TimeOfDay.Hours,
        $TimeOfDay.Minutes,
        $TimeOfDay.Seconds,
        $TimeOfDay.Milliseconds
    )
    $d = Get-Date
    $isTomorrow = $TimeOfDay -le $d.TimeOfDay
    $d = [datetime]::new(
        $d.Year,
        $d.Month,
        $d.Day,
        $TimeOfDay.Hours,
        $TimeOfDay.Minutes,
        $TimeOfDay.Seconds,
        $TimeOfDay.Milliseconds
    )
    if ($isTomorrow) {
        $d = $d.AddDays(1)
    }
    Write-Output $d
}


<#
.SYNOPSIS
    Get the previous occurence of a specified time.

.DESCRIPTION
    Returns the last point of time from now that has the specified time parts.

.PARAMETER TimeOfDay
    A TimeSpan object specifying the time parts. The Days member is ignored.

    Note that a string in the form of "hh:mm[:ss[.ff]]" can also be used. For more details, see the Remarks section at <https://learn.microsoft.com/en-us/dotnet/api/system.timespan.parse>.

.INPUTS
    None

.OUTPUTS
    DateTime
#>
function Get-PreviousTime {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        [timespan]$TimeOfDay
    )
    $TimeOfDay = [timespan]::new(
        0,  # ignore Days
        $TimeOfDay.Hours,
        $TimeOfDay.Minutes,
        $TimeOfDay.Seconds,
        $TimeOfDay.Milliseconds
    )
    $d = Get-Date
    $isYesterday = $TimeOfDay -ge $d.TimeOfDay
    $d = [datetime]::new(
        $d.Year,
        $d.Month,
        $d.Day,
        $TimeOfDay.Hours,
        $TimeOfDay.Minutes,
        $TimeOfDay.Seconds,
        $TimeOfDay.Milliseconds
    )
    if ($isYesterday) {
        $d = $d.AddDays(-1)
    }
    Write-Output $d
}


Export-ModuleMember -Function *-*
