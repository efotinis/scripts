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


# Get objects whose named property matches all specified wildcard patterns.
filter Get-AllLikeProperty {
    param(
        [string]$Name,
        [string[]]$Pattern
    )
    $val = $_.$Name
    foreach ($p in $Pattern) {
        if ($val -notlike $p) {
            return
        }
    }
    $_
}


# Get objects whose named property matches any specified wildcard patterns.
filter Get-AnyLikeProperty {
    param(
        [string]$Name,
        [string[]]$Pattern
    )
    $val = $_.$Name
    foreach ($p in $Pattern) {
        if ($val -like $p) {
            $_
            return
        }
    }
}


# Get objects whose named property matches all specified regex patterns.
filter Get-AllMatchProperty {
    param(
        [string]$Name,
        [string[]]$Pattern
    )
    $val = $_.$Name
    foreach ($p in $Pattern) {
        if ($val -notmatch $p) {
            return
        }
    }
    $_
}


# Get objects whose named property matches any specified regex patterns.
filter Get-AnyMatchProperty {
    param(
        [string]$Name,
        [string[]]$Pattern
    )
    $val = $_.$Name
    foreach ($p in $Pattern) {
        if ($val -match $p) {
            $_
            return
        }
    }
}


# Filter pipeline items besed on property value range.
# The property can be specified either as a name (string) or be calculated 
# with a scriptblock (with $_ representing the current item).
# Start/end values are included unless ExcludeStart/ExcludeEnd are specified.
# An error is generated if the specified property did not exist or was not 
# calculated for some input objects.
function Get-InRangeProperty {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]$InputObject,
        [Parameter(Mandatory, Position=1)]$Property,  # name or scriptblock
        [Parameter(Mandatory, Position=2)]$Start,
        [Parameter(Mandatory, Position=3)]$End,
        [Alias('xs')][switch]$ExcludeStart,
        [Alias('xe')][switch]$ExcludeEnd
    )
    begin {
        if ($Start -gt $End) {
            throw "start value ($Start) must be less than or equal to end value ($End)"
        }
        $missing = $false
        $startCheck = if ($ExcludeStart) {
            { $value -gt $Start }
        } else {
            { $value -ge $Start }
        }
        $endCheck = if ($ExcludeEnd) {
            { $value -lt $End }
        } else {
            { $value -le $End }
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
- SubSize: Generate arrays of length SubSize, except the last may be smaller.
- GroupCount: Generate no more than GroupCount arrays of equal size, except the
  last may be smaller.
- HeadSize: Produce two arrays, with the first containing no more than HeadSize
  items and the second the rest.

Based on:
    https://gallery.technet.microsoft.com/scriptcenter/Split-an-array-into-parts-4357dcc1
#>

function Split-Array {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [object[]]$InputObject,

        [Parameter(Mandatory, ParameterSetName='SubSize')]
        [ValidateRange(1, [int]::MaxValue)]
        [int]$SubSize,
        
        [Parameter(Mandatory, ParameterSetName='GroupCount')]
        [ValidateRange(1, [int]::MaxValue)]
        [int]$GroupCount,
        
        [Parameter(Mandatory, ParameterSetName='HeadSize')]
        [ValidateRange(0, [int]::MaxValue)]
        [int]$HeadSize
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
                ,$items.GetRange(0, $HeadSize)
                ,$items.GetRange($HeadSize, $totalCount - $HeadSize)
                return
            }
            'GroupCount' {
                $SubSize = [Math]::Ceiling($totalCount / $GroupCount)
                $GroupCount = [Math]::Ceiling($totalCount / $SubSize)
            }
            'SubSize' {
                $GroupCount = [Math]::Ceiling($totalCount / $SubSize)
            }
        }
        for ($i = 0; $i -lt $GroupCount; ++$i) {
            $beg = $i * $SubSize
            $end = [Math]::Min(($i + 1) * $SubSize, $totalCount)
            ,$Items.GetRange($beg, $end - $beg)
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
