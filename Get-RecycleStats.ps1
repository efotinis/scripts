<#
.SYNOPSIS
    Show Recycle Bin item statistics.

.DESCRIPTION
    Displays count and total size of Recycle Bin items, grouped by certain
    properties.

.PARAMETER GroupBy
    The property to group items with. One of the following:
        - Drive: The original location drive.
        - Type: The file type.

.INPUTS
    None.

.OUTPUTS
    Custom objects.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('Drive', 'Type')]
    [string]$GroupBy
)
switch ($GroupBy) {
    'Drive' {
        $props = @('Original Location', 'Size')
        $grouping = { Split-Path $_.OriginalLocation -Qualifier }
        $groupTitle = 'Drive'
    }
    'Type' {
        $props = @('Item type', 'Size')
        $grouping = 'Itemtype'
        $groupTitle = 'Type'
    }
}
Get-RecycledItem $props |
    group $grouping |
    foreach {
        $bytes = $_.Group | measure -sum Size | % sum
        [PSCustomObject]@{
            Count = $_.Group.Count
            Bytes = $Bytes
            Size = ConvertTo-NiceSize $Bytes
            $groupTitle = $_.Name
        }
    }
