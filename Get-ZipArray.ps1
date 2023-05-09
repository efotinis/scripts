<#
.SYNOPSIS
    Zip items from multiple arrays.

.DESCRIPTION
    Returns arrays of items from the same positions in each input array, similar to Python's zip().

.PARAMETER InputObject
    Array of input arrays.

.PARAMETER IgnoreLonger
    Only return items up to the index of the shortest input array. This is the default behavior, however a warning is issued unless this switch is used.

.PARAMETER FillShorter
    Return all items, up to the length of the longest input array. Arrays with fewer items use this as a substitute.

.INPUTS
    None

.OUTPUTS
    Object arrays
#>

[CmdletBinding(DefaultParameterSetName = 'Ignore')]
param(
    [Parameter(Mandatory)]
    [object[]]$InputObject,

    [Parameter(ParameterSetName = 'Ignore')]
    [switch]$IgnoreLonger,

    [Parameter(ParameterSetName = 'Fill')]
    [object]$FillShorter
)

$m = $InputObject | Measure-Object -Minimum -Maximum Count
$minSize = $m.Minimum
$maxSize = $m.Maximum

if ($PSCmdlet.ParameterSetName -eq 'Ignore') {

    for ($i = 0; $i -lt $minSize; ++$i) {
        Write-Output (,@($InputObject | % { $_[$i] }))
    }

    if ($minSize -lt $maxSize -and -not $IgnoreLonger) {
        Write-Warning "Items from longer arrays were ignored."
    }

} else {

    for ($i = 0; $i -lt $maxSize; ++$i) {
        Write-Output (,@($InputObject | % {
            if ($i -lt $_.Count) {
                $_[$i]
            } else {
                $FillShorter
            }
        }))
    }

}
