<#
.SYNOPSIS
    Perform prime factorization.

.DESCRIPTION
    Get the prime factors of an integer. Returns one or more object with these properties:
        - Factor    Prime factor.
        - Power     Factor power.
        - Product   Calculated value of Factor raised to Power.

.PARAMETER InputObject
    Input number. Must be >= 2. Can be passed via the pipeline.

.INPUTS
    Integer (32-bit).

.OUTPUTS
    PSCustomObject.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [ValidateRange(2, [int]::MaxValue)]
    [int]$InputObject
)
process {
    $value = $InputObject
    $threshold = [Math]::Sqrt($value) -as [int]  # need not check higher than sqrt
    for ($n = 2; $value -gt 1 -and $n -lt $threshold; ++$n) {
        for ($m = 0; $value % $n -eq 0; ++$m) {
            $value /= $n
        }
        if ($m) {
            [PSCustomObject]@{
                Factor = $n
                Power = $m
                Product = [Math]::Pow($n, $m)
            }
        }
    }
    if ($value -gt 1) {  # threshold exceeded
        [PSCustomObject]@{
            Factor = $value
            Power = 1
            Product = $value
        }
    }
}
