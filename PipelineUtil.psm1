<#
.SYNOPSIS
    Pipeline utilities.

.DESCRIPTION
    Various pipeline filters.
#>


# Get an object property by name or by evaluating a scriptblock. 
# In the case of a scriptblock, the object is available as $_ and 
# if multiple values are returned, only the first one is used.
# Returns $null on error or if missing.
function CalculateProperty ($Object, $Property) {
    if ($Property -is [scriptblock]) {
        $values = $Property.InvokeWithContext(
            $null, 
            [psvariable]::new('_', $Object)
        )
        if ($values.Count -gt 0) {
            return $values[0]
        } else {
            return $null
        }
    }
    if (Get-Member -InputObject $Object -Name $Property) {
        return $Object.$Property
    } else {
        return $null
    }
}


function ReportPartiallyMissingProperty ($Property) {
    if ($Property -is [scriptblock]) {
        Write-Error "Scriptblock did not return value for some objects"
    } else {
        Write-Error "Named property not found in some objects: $Property"
    }
}


# Reverse pipeline.
function Get-ReverseArray
{
    $items = @($input)
    [array]::reverse($items)
    $items
}


# Shuffle pipeline.
function Get-ShuffleArray
{
    $items = @($input)
    if ($items.Count) {
        $items | Get-Random -Count $items.Length
    }
}


# Pick random items from the pipeline in their original order.
function Get-OrderedSubset ([int]$Count) {
    $items = @($input)
    if ($items.length) {
        0..($items.Count - 1) | Get-Random -Count $Count | Sort-Object | % {
            $items[$_]
        }
    }
}


# Filter items with a unique property (first found wins).
# The property can be specified either as a name (string) or be calculated 
# with a scriptblock (with $_ representing the current item).
# An error is generated if the specified property did not exist or was not 
# calculated for some input objects.
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
            $value = CalculateProperty $item $Property
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
    }
}



# Filter pipeline items based on property value range.
# The property can be specified either as a name (string) or be calculated 
# with a scriptblock (with $_ representing the current item).
# The range can be specified as either a start/end or with a center and radius.
# Boundaries are included unless ExcludeStart/ExcludeEnd are specified.
# An error is generated if the specified property did not exist or was not 
# calculated for some input objects.
function Get-InRangeProperty {
    [CmdletBinding(DefaultParameterSetName='StartEnd')]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]$InputObject,
        [Parameter(Mandatory, Position=1)]$Property,  # name or scriptblock
        [Parameter(Mandatory, Position=2, ParameterSetName='StartEnd')]$Start,
        [Parameter(Mandatory, Position=3, ParameterSetName='StartEnd')]$End,
        [Parameter(Mandatory, Position=2, ParameterSetName='CenterRadius')]$Center,
        [Parameter(Mandatory, Position=3, ParameterSetName='CenterRadius')]$Radius,
        [Alias('xs')][switch]$ExcludeStart,
        [Alias('xe')][switch]$ExcludeEnd
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
        $value = CalculateProperty $_ $Property
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


# Add numeric index to objects.
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
Split collection into sub-arrays, depending on the specified parameter:
- GroupSize: Generate arrays of length GroupSize, except the last may be smaller.
- GroupCount: Generate no more than GroupCount arrays of equal size, except the
  last may be smaller.
- HeadSize: Produce two arrays, with the first containing no more than HeadSize
  items and the second the rest.
- TailSize: Produce two arrays, with the second containing no more than TailSize
  items and the first the rest.

Based on:
    https://gallery.technet.microsoft.com/scriptcenter/Split-an-array-into-parts-4357dcc1
#>

function Split-Array {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [object[]]$InputObject,

        [Parameter(Mandatory, ParameterSetName='GroupSize')]
        [ValidateRange(1, [int]::MaxValue)]
        [int]$GroupSize,
        
        [Parameter(Mandatory, ParameterSetName='GroupCount')]
        [ValidateRange(1, [int]::MaxValue)]
        [int]$GroupCount,
        
        [Parameter(Mandatory, ParameterSetName='HeadSize')]
        [ValidateRange(0, [int]::MaxValue)]
        [int]$HeadSize,
        
        [Parameter(Mandatory, ParameterSetName='TailSize')]
        [ValidateRange(0, [int]::MaxValue)]
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


<#function cc-cc {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
            $InputObject,
        [scriptblock] $Code
    )
    process {
        "  process block: $_"
        "code evaluation: $(. $Code)"
    }
}#>
function Test-Cc {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
            $InputObject,
        [scriptblock] $Code
    )
    process {
        "  process block: $InputObject"
        "code evaluation: $(. $Code)"
    }
}
#1..3 | cc-cc -x { $_ }

# ----------------------------------------------------------------


Export-ModuleMember -Function *-*
