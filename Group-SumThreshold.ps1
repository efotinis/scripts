<#
.SYNOPSIS
    Group objects using a threshold sum value.

.DESCRIPTION
    Returns groups of adjacent objects that have a property sum less than or equal to a specified threshold. If a single object exceeds the threshold, it is returned in a group of its own and a warning is issued.

    The returned objects contain these properties:
        - Count     Number of items in the group.
        - Sum       The value sum of the group items.
        - Group     The objects of the group.

    See AllowOvershoot for an alternate threshold check method.

.PARAMETER InputObject
    Input object. Use the pipeline to specify multiple objects.

.PARAMETER Property
    The object property to use. Can be a property name (string) or a scriptblock to calculate the value of each object.

.PARAMETER Value
    A floating point number denoting the threshold for generating groups.

.PARAMETER AllowOvershoot
    Groups are returned when the value sum becomes greater than or equal to the threshold. No warnings are generated in this case.

.INPUTS
    Object

.OUTPUTS
    PSCustomObject

.EXAMPLE
    PS> ls G:\youtube\AVGN\ | .\Group-SumThreshold.ps1 length 4.37gb

    Count        Sum Group
    -----        --- -----
        6 4146021523 {Season 01.mp4, Season 02.mp4, Season 03...
        7 4299735285 {Season 07.mp4, Season 08.mp4, Season 09...
        2 1812239236 {Season 14.mp4, Season 15.mp4}

    This example demonstrates grouping a set of files to fit in DVDs. We specify `length` (i.e. file size) as the counting value and 4.37 GiB as the maximum group size (nominal DVD capacity). This results in three groups with varying number of files each. Note that no warnings were generated, therefore no group size exceeded the DVD size.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    $InputObject,

    [Parameter(Position = 0)]
    [object]$Property,

    [Parameter(Mandatory, Position = 1)]
    [double]$Value,

    [Alias('Over')]
    [switch]$AllowOvershoot
)
begin {
    $items = [System.Collections.ArrayList]::new()
    $total = 0
    function Flush {
        [PSCustomObject]@{
            Count = $items.Count
            Sum = $total
            Group = @($items)
        }
        if ($total -gt $Value -and -not $AllowOvershoot) {
            Write-Warning "Sum exceeds threshold: $total > $Value"
        }
        $items.Clear()
        $script:total = 0
    }
}
process {
    $current = Get-ObjectValue -Property $Property -InputObject $InputObject
    if ($AllowOvershoot) {
        # add first, then check threshold
        [void]$items.Add($InputObject)
        $total += $current
        if ($total -ge $Value) {
            Flush
        }
    } elseif ($total + $current -lt $Value) {
        # adding below threshold
        [void]$items.Add($InputObject)
        $total += $current
    } elseif ($items.Count -eq 0) {
        # single item exceeding threshold; flush it
        [void]$items.Add($InputObject)
        $total += $current
        Flush
    } else {
        # flush existing and add new
        Flush
        [void]$items.Add($InputObject)
        $total += $current
    }
}
end {
    if ($items.Count) {
        Flush
    }
}
