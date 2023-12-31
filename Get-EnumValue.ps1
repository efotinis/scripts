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
    foreach ($name in $Type.GetEnumNames()) {
        $value = $Type::$name -as [int]
        $a = [ordered]@{
            Value = $value
        }
        if ($Hexadecimal) {
            $a.Hex = '0x' + $value.ToString('x')
        }
        if ($Binary) {
            $s = [Convert]::ToString($value, 2).PadLeft(32, '0') -replace '0','.'
            for ($i = 0; $i -lt 32; $i += 8) {
                if ($s[$i] -eq '.') {
                    $s = $s.Substring(0, $i) + ":" + $s.Substring($i + 1)
                }
            }
            $a.Bin = $s
        }
        $a.Name = $name
        [PSCustomObject]$a
    }
}
