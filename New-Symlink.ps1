<#
    Create symlinks of specified items.
    Create destination directory if it does not exist.
    New items can optionally have a leading numeric index
    and be shuffled.
#>

param(
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
