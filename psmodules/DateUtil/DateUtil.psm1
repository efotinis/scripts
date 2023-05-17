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


# Convert from 'M/d/(yy)yy' or 'M.d.(yy)yy' to DateTime.
# 2-digit years are assumed to be 20xx.
function ConvertFrom-USDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Date,

        [switch]$Scan  # match substring anywhere within input
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


#
<#
.SYNOPSIS
    Get the next occurence of a specified time.

.DESCRIPTION
    Returns the next next point of time from now that has the specified time parts.

.PARAMETER TimeOfDay
    A TimeSpan object specifying the time parts. The Days member is ignored.

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


Export-ModuleMember -Function *-*
