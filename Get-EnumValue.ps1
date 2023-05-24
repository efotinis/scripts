param(
    [Parameter(Mandatory, ValueFromPipeline)]
    $Type,

    [switch]$Hexadecimal,

    [switch]$Binary
)
$Type.GetEnumNames() | % {
    $Value = [int]($Type::$_)
    $a = [ordered]@{
        Value=$Value
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
