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


Export-ModuleMember -Function *-*
