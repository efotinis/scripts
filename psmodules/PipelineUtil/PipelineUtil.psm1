# Pipeline/collection utilities.


<#
.SYNOPSIS
    Get the value of an object property.
.DESCRIPTION
    Returns either the value of a property specified by name or a value
    calculated by a scriptblock using the object as an argument.
.PARAMETER InputObject
    Input object. Can accept multiple values via the pipeline.
.PARAMETER Property
    The name of a property (string) or a scriptblock that accepts the current
    object and returns a calculated value. If the property name does not exist
    or the scriptblock does not return anything, $null is returned. If the
    scriptblock returns multiple values, only the first is returned.
.INPUTS
    Any object.
.OUTPUTS
    Any object.
#>
function Get-ObjectValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        $Property,

        [Parameter(Mandatory, Position = 1, ValueFromPipeline)]
        $InputObject
    )
    process {
        if ($Property -is [scriptblock]) {
            $values = $Property.InvokeWithContext(
                $null,
                [psvariable]::new('_', $InputObject)
            )
            if ($values.Count -gt 0) {
                Write-Output $values[0]
            } else {
                Write-Output $null
            }
        } else {
            if (Get-Member -InputObject $InputObject -Name $Property) {
                Write-Output $InputObject.$Property
            } else {
                Write-Output $null
            }
        }
    }
}


# Write error regarding missing property specifier (string or scriptblock).
function ReportPartiallyMissingProperty ($Property) {
    if ($Property -is [scriptblock]) {
        Write-Error "Scriptblock did not return value for some objects"
    } else {
        Write-Error "Named property not found in some objects: $Property"
    }
}


<#
.SYNOPSIS
    Reverse the order of pipelined objects.
#>
function Get-ReverseArray
{
    $items = @($input)
    [array]::reverse($items)
    $items
}


<#
.SYNOPSIS
    Randomize the order of pipelined objects.
#>
function Get-ShuffleArray
{
    $items = @($input)
    if ($items.Count) {
        $items | Get-Random -Count $items.Length
    }
}


<#
.SYNOPSIS
    Pick random items from a list in their original order.
.PARAMETER Count
    Number of items to get. Must be > 0. Specifying a number greater or equal
    to the input size is not an error and simply retuns the entire input as is.
    Default is 1.
#>
function Get-OrderedSubset ([int]$Count = 1) {
    $items = @($input)
    if ($items.length) {
        0..($items.Count - 1) | Get-Random -Count $Count | Sort-Object | % {
            $items[$_]
        }
    }
}


<#
.SYNOPSIS
    Get items with a unique property.
.DESCRIPTION
    Select objects that have a unique property. If there are multiple equal
    input items, the first is selected.
.PARAMETER InputObject
    Input object. Can specify either a collection argument or pass via the
    pipeline.
.PARAMETER Property
    The property that designates uniqueness. Possible types:
        - string: Property name.
        - scriptblock: Accepts the current item as $_ and returns a value.
    If the property was missing or not calculated for any input items, an error
    is generated.
#>
function Get-UniqueByProperty {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        $InputObject,

        [Parameter(Mandatory, Position=1)]
        $Property  # name or scriptblock
    )
    begin {
        $seen = [System.Collections.Generic.HashSet[object]]@()
        $missing = $false
    }
    process {
        foreach ($item in $InputObject) {
            $value = Get-ObjectValue $Property $item
            if ($null -eq $value) {
                $missing = $true
            } elseif ($seen.Add($value)) {
                Write-Output $item
            }
        }
    }
    end {
        if ($missing) {
            ReportPartiallyMissingProperty $Property
        }
    }
}


# ----------------------------------------------------------------


function AllLike ($Value, [string[]]$Pattern) {
    foreach ($p in $Pattern) {
        if ($Value -notlike $p) {
            return $false
        }
    }
    return $true
}


function AnyLike ($Value, [string[]]$Pattern) {
    foreach ($p in $Pattern) {
        if ($Value -like $p) {
            return $true
        }
    }
    return $false
}


function AllMatch ($Value, [string[]]$Pattern) {
    foreach ($p in $Pattern) {
        if ($Value -notmatch $p) {
            return $false
        }
    }
    return $true
}


function AnyMatch ($Value, [string[]]$Pattern) {
    foreach ($p in $Pattern) {
        if ($Value -match $p) {
            return $true
        }
    }
    return $false
}


<#
.SYNOPSIS
    Get objects whose property matches specified criteria.
.DESCRIPTION
    Perform wildcard or regex pattern checks on a specified property of input
    objects and return those that satisfy them.

    To get the inverse of a multi-pattern condition, use the following
    complementary option pairs:
        - LikeAny / NotLikeAll
        - LikeAll / NotLikeAny
        - MatchAny / NotMatchAll
        - MatchAll / NotMatchAny
.PARAMETER InputObject
    Input objects. Must be passed via the pipeline.
.PARAMETER Name
    The name of the property to test.
.PARAMETER Like
    A single wildcard pattern to match.
.PARAMETER NotLike
    A single wildcard pattern to not match.
.PARAMETER LikeAny
    Two or more wildcard patterns to match any of.
.PARAMETER NotLikeAny
    Two or more wildcard patterns to not match any of.
.PARAMETER LikeAll
    Two or more wildcard patterns to match all of.
.PARAMETER NotLikeAll
    Two or more wildcard patterns to not match all of.
.PARAMETER Match
    A single regex pattern to match.
.PARAMETER NotMatch
    A single regex pattern to not match.
.PARAMETER MatchAny
    Two or more regex patterns to match any of.
.PARAMETER NotMatchAny
    Two or more regex patterns to not match any of.
.PARAMETER MatchAll
    Two or more regex patterns to match all of.
.PARAMETER NotMatchAll
    Two or more regex patterns to not match all of.
#>
function Get-IfProperty {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        $InputObject,

        [Parameter(Mandatory, Position = 0)]
        [string]$Name,

        [Parameter(Mandatory, ParameterSetName = 'Like')]
        [string]$Like,

        [Parameter(Mandatory, ParameterSetName = 'NotLike')]
        [string]$NotLike,

        [Parameter(Mandatory, ParameterSetName = 'LikeAny')]
        [string[]]$LikeAny,

        [Parameter(Mandatory, ParameterSetName = 'NotLikeAny')]
        [string[]]$NotLikeAny,

        [Parameter(Mandatory, ParameterSetName = 'LikeAll')]
        [string[]]$LikeAll,

        [Parameter(Mandatory, ParameterSetName = 'NotLikeAll')]
        [string[]]$NotLikeAll,

        [Parameter(Mandatory, ParameterSetName = 'Match')]
        [string]$Match,

        [Parameter(Mandatory, ParameterSetName = 'NotMatch')]
        [string]$NotMatch,

        [Parameter(Mandatory, ParameterSetName = 'MatchAny')]
        [string[]]$MatchAny,

        [Parameter(Mandatory, ParameterSetName = 'NotMatchAny')]
        [string[]]$NotMatchAny,

        [Parameter(Mandatory, ParameterSetName = 'MatchAll')]
        [string[]]$MatchAll,

        [Parameter(Mandatory, ParameterSetName = 'NotMatchAll')]
        [string[]]$NotMatchAll

        <#[ParameterSetName('Options')]
        [hashtable]$Options#>
    )
    begin {
        switch ($PSCmdLet.ParameterSetName) {
            'Like' {
                $pattern = @($Like)
                $checker = Get-Item -LiteralPath Function:AnyLike
                $invert = $false
            }
            'NotLike' {
                $pattern = @($NotLike)
                $checker = Get-Item -LiteralPath Function:AllLike
                $invert = $true
            }
            'LikeAny' {
                $pattern = $LikeAny
                $checker = Get-Item -LiteralPath Function:AnyLike
                $invert = $false
            }
            'NotLikeAny' {
                $pattern = $NotLikeAny
                $checker = Get-Item -LiteralPath Function:AllLike
                $invert = $true
            }
            'LikeAll' {
                $pattern = $LikeAll
                $checker = Get-Item -LiteralPath Function:AllLike
                $invert = $false
            }
            'NotLikeAll' {
                $pattern = $NotLikeAll
                $checker = Get-Item -LiteralPath Function:AnyLike
                $invert = $true
            }
            'Match' {
                $pattern = @($Match)
                $checker = Get-Item -LiteralPath Function:AnyMatch
                $invert = $false
            }
            'NotMatch' {
                $pattern = @($NotMatch)
                $checker = Get-Item -LiteralPath Function:AllMatch
                $invert = $true
            }
            'MatchAny' {
                $pattern = $MatchAny
                $checker = Get-Item -LiteralPath Function:AnyMatch
                $invert = $false
            }
            'NotMatchAny' {
                $pattern = $NotMatchAny
                $checker = Get-Item -LiteralPath Function:AllMatch
                $invert = $true
            }
            'MatchAll' {
                $pattern = $MatchAll
                $checker = Get-Item -LiteralPath Function:AllMatch
                $invert = $false
            }
            'NotMatchAll' {
                $pattern = $NotMatchAll
                $checker = Get-Item -LiteralPath Function:AnyMatch
                $invert = $true
            }
        }
    }
    process {
        if ((& $checker $_.$Name $pattern) -xor $invert) {
            $InputObject
        }
        # TODO: USe ReportPartiallyMissingProperty
    }
}


<#
.SYNOPSIS
    Get objects where a property is within a range.
.DESCRIPTION
    Filter pipeline objects based on a property value range. The property can
    be specified either as a name (string) or be calculated with a scriptblock.

    The range can be specified as either a start/end or a center/radius.
    Boundaries are included by default.

    An error is generated if the specified property did not exist or was not
    calculated for some input objects.
.PARAMETER InputObject
    Input objects. Must use the pipeline to specify a collection.
.PARAMETER Property
    The name (string) of the property to test or a scriptblock to calculate
    a value per object (with $_ representing the current object).
.PARAMETER Start
    The range start.
.PARAMETER End
    The range end.
.PARAMETER Center
    The range center.
.PARAMETER Radius
    The range radius.
.PARAMETER ExcludeStart
    Exclude the start of the range.
.PARAMETER ExcludeEnd
    Exclude the end of the range.
#>
function Get-InRangeProperty {
    [CmdletBinding(DefaultParameterSetName='StartEnd')]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        $InputObject,

        [Parameter(Mandatory, Position=1)]
        $Property,

        [Parameter(Mandatory, Position=2, ParameterSetName='StartEnd')]
        $Start,

        [Parameter(Mandatory, Position=3, ParameterSetName='StartEnd')]
        $End,

        [Parameter(Mandatory, Position=2, ParameterSetName='CenterRadius')]
        $Center,

        [Parameter(Mandatory, Position=3, ParameterSetName='CenterRadius')]
        $Radius,

        [Alias('xs')]
        [switch]$ExcludeStart,

        [Alias('xe')]
        [switch]$ExcludeEnd
    )
    begin {
        switch ($PSCmdlet.ParameterSetName) {
            'StartEnd' {
                if ($Start -gt $End) {
                    throw "start value ($Start) must be less than or equal to end value ($End)"
                }
                $minValue = $Start
                $maxValue = $End
            }
            'CenterRadius' {
                # NOTE: Radius must be to the right of operator to coerse
                # to number, since a negative arg is bound as a string
                # FIXME: This however causes an error when Radius is a TimeSpan.
                if (0 -gt $Radius) {
                    throw "radius value ($Radius) must be non-negative"
                }
                $minValue = $Center - $Radius
                $maxValue = $Center + $Radius
            }
        }
        $missing = $false
        $startCheck = if ($ExcludeStart) {
            { $value -gt $minValue }
        } else {
            { $value -ge $minValue }
        }
        $endCheck = if ($ExcludeEnd) {
            { $value -lt $maxValue }
        } else {
            { $value -le $maxValue }
        }
    }
    process {
        $value = Get-ObjectValue $Property $_
        if ($null -eq $value) {
            $missing = $true
        } elseif ($startCheck.Invoke($value) -and $endCheck.Invoke($value)) {
            Write-Output $_
        }
    }
    end {
        if ($missing) {
            ReportPartiallyMissingProperty $Property
        }
    }
}


# ----------------------------------------------------------------


<#
.SYNOPSIS
    Add numeric index member to objects passed via the pipeline.
.PARAMETER Name
    The name of the index member property to add. Default is 'Index'.
.PARAMETER Start
    The start of the index values. Default is 0.
.PARAMETER Step
    The step increment of the index values. Default is 1.
.PARAMETER PassThru
    Output the processed objects to the pipeline.
#>

function Add-IndexMember {
    param(
        [string]$Name = 'Index',
        [int]$Start = 0,
        [int]$Step = 1,
        [switch]$PassThru
    )
    begin {
        $i = $Start
    }
    process {
        $_ | Add-Member -NotePropertyName $Name -NotePropertyValue $i -PassThru:$PassThru
        $i += $Step
    }
}


# ----------------------------------------------------------------


<#
.SYNOPSIS
    Split collection of objects to sub-arrays.
.DESCRIPTION
    Use to split input objects into groups or head/tail and rest.
.PARAMETER InputObject
    Input objects. Can either specify a collection or pass via the pipeline.
.PARAMETER GroupSize
    Evenly split into arrays of this size (>=1). The last array may be smaller.
.PARAMETER GroupCount
    Evenly split into this number (>=1) of arrays. The last array may be smaller.
.PARAMETER HeadSize
    Split into two arrays, with the first no bigger than specified (>=0).
.PARAMETER TailSize
    Split into two arrays, with the second no bigger than specified (>=0).
.NOTES
    Inspired by:
        https://gallery.technet.microsoft.com/scriptcenter/Split-an-array-into-parts-4357dcc1
#>

function Split-Array {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [object[]]$InputObject,

        [Parameter(Mandatory, ParameterSetName='GroupSize')]
        [ValidateRange(1, [int]::MaxValue)]
        [Alias('GS')]
        [int]$GroupSize,

        [Parameter(Mandatory, ParameterSetName='GroupCount')]
        [ValidateRange(1, [int]::MaxValue)]
        [Alias('GC')]
        [int]$GroupCount,

        [Parameter(Mandatory, ParameterSetName='HeadSize')]
        [ValidateRange(0, [int]::MaxValue)]
        [Alias('HS')]
        [int]$HeadSize,

        [Parameter(Mandatory, ParameterSetName='TailSize')]
        [ValidateRange(0, [int]::MaxValue)]
        [Alias('TS')]
        [int]$TailSize
    )
    begin {
        $items = [System.Collections.ArrayList]::new()
    }
    process {
        $items.AddRange($InputObject)
    }
    end {
        $totalCount = $items.Count
        if ($totalCount -eq 0) {
            Write-Warning 'No input items.'
            return
        }
        switch ($PSCmdlet.ParameterSetName) {
            'HeadSize' {
                $HeadSize = [Math]::Min($HeadSize, $totalCount)
            }
            'TailSize' {
                $HeadSize = [Math]::Max(0, $totalCount - $TailSize)
            }
            'GroupCount' {
                $GroupSize = [Math]::Ceiling($totalCount / $GroupCount)
                $GroupCount = [Math]::Ceiling($totalCount / $GroupSize)
            }
            'GroupSize' {
                $GroupCount = [Math]::Ceiling($totalCount / $GroupSize)
            }
        }
        if ($PSCmdlet.ParameterSetName -in 'GroupCount','GroupSize') {
            for ($i = 0; $i -lt $GroupCount; ++$i) {
                $beg = $i * $GroupSize
                $end = [Math]::Min(($i + 1) * $GroupSize, $totalCount)
                Write-Output (,$Items.GetRange($beg, $end - $beg))
            }
        } else {
            Write-Output (,$items.GetRange(0, $HeadSize))
            Write-Output (,$items.GetRange($HeadSize, $totalCount - $HeadSize))
        }
    }

}


<#
# Seperate items based on delimiters.
function Group-HeadTail {
    #[CmdletBinding()]
    param(
        #[Parameter(Mandatory, ValueFromPipeline)]
        #    $InputObject,
        #[Parameter(Mandatory)]
            [scriptblock] $Header,  # header identification test
        [switch] $Flat  # generate flat arrays instead of objects
    )
    begin {
        $head, $tail = @(), @()
        function flush {
            if ($head.Count) {
                if ($Flat) {
                    ,($head + $tail)
                } else {
                    [PSCustomObject]@{ Head = $head; Tail = $tail }
                }
            } elseif ($tail.Count) {
                Write-Warning "missing header before items: $($tail -join ',')"
            }
        }
    }
    process {
        Write-Host "process: `$_ = $_"
        if (& $Header) {
            flush
            $head, $tail = @($_), @()
        } else {
            $tail += $_
        }
    }
    end {
        flush
    }
}#>


# ----------------------------------------------------------------


Export-ModuleMember -Function *-*
