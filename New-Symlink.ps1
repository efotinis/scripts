<#
.SYNOPSIS
    Create symlinks with optional index and ability to shuffle.

.DESCRIPTION
    Creates file/directory symlinks. An optional index can be prepended to the filenames. The output order of the items can be randomized.

.PARAMETER Items
    Array of source file/directory items.

.PARAMETER Destination
    Output directory to place all new links into. Will be created if missing.

.PARAMETER Index
    Add increasing, 1-based numeric index at the start of output names. The index is based on their location in the input array and has a dot after it (e.g. "001. "). The number is padded with enough zeroes to fit the largest index.

.PARAMETER Shuffle
    Shuffle indexes of output items.

.INPUTS
    System.IO.FileSystemInfo[]

.OUTPUTS
    System.IO.FileSystemInfo[]
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [System.IO.FileSystemInfo[]]$Items,

    [string]$Destination = '.',

    [switch]$Index,

    [switch]$Shuffle
)

if (-not (Test-Path -Type Container $Destination)) {
    if (-not (New-Item -Type Container $Destination)) {
        return
    }
}

if ($Shuffle) {
    $Items = $Items | Get-Random -Count $Items.Length
}

$count = $Items.Length
$indexFormat = 'D' + $count.ToString().Length
function NewName ($item, $i) {
    if ($Index) {
        $i.ToString($indexFormat) + '. ' + $item.Name
    } else {
        $item.Name
    }
}

$i = 1
foreach ($item in $Items) {
    $value = $item.FullName -replace '\[','[[]'  # HACK: wildcards must be escaped for some reason
    New-Item -Path $Destination -Name (NewName $Item $i) -Type SymbolicLink -Value $value
    ++$i
}
