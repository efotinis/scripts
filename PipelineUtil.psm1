<#
.SYNOPSIS
    Pipeline utilities.

.DESCRIPTION
    Various pipeline filters.
#>


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
    0..($items.Count - 1) | Get-Random -Count $Count | Sort-Object | % {
        $items[$_]
    }
}


<# 
function Get-UniqueByProperty ([string]$Name) {
    begin {
    }
    process {
    }
}#>


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
