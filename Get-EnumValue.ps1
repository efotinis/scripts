<#
.SYNOPSIS
    List enum values.

.DESCRIPTION
    Outputs the names and values of an enumeration.

.PARAMETER Type
    The enumeration type. Multiple items can be specified via the pipeline.

.PARAMETER Hexadecimal
    Include hexadecimal representation of values in output.

.PARAMETER Binary
    Include binary representation of values in output.

.INPUTS
    Type

.OUTPUTS
    PSCustomObject
#>
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    $Type,

    [switch]$Hexadecimal,

    [switch]$Binary
)
process {
    $Type.GetEnumNames() | % {
        $Value = [int]($Type::$_)
        $a = [ordered]@{
            Value = $Value
        }
        if ($Hexadecimal) {
            $a.Hex = $Value.ToString('x8')
        }
        if ($Binary) {
            $a.Bin = [Convert]::ToString($Value, 2).PadLeft(32, '0') -replace '0','.'
        }
        $a.Name = $_
        [PSCustomObject]$a
    }
}
