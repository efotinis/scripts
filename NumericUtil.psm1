<#
.SYNOPSIS
    Perform prime factorization.

.DESCRIPTION
    Get the prime factors of an integer. Returns one or more object with these properties:
        - Factor    Prime factor.
        - Power     Factor power.
        - Product   Calculated value of Factor raised to Power.

    Uses the naive method of testing all numbers up to the square root of the input, so it is not time-efficient.

.PARAMETER InputObject
    Input number. Must be >= 2. Can be passed via the pipeline.

.INPUTS
    Int32.

.OUTPUTS
    PSCustomObject.
#>
function Get-PrimeFactor {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateRange(2, [int]::MaxValue)]
        [int]$InputObject
    )
    begin {
        function Output ($Factor, $Power) {
            [PSCustomObject]@{
                Factor = $Factor
                Power = $Power
                Product = [Math]::Pow($Factor, $Power)
            }
        }
    }
    process {
        $value = $InputObject
        $threshold = [Math]::Sqrt($value) -as [int]  # need not check higher than sqrt
        for ($n = 2; $value -gt 1 -and $n -lt $threshold; ++$n) {
            for ($m = 0; $value % $n -eq 0; ++$m) {
                $value /= $n
            }
            if ($m) {
                Output $n $m
            }
        }
        if ($value -gt 1) {  # threshold exceeded
            Output $value 1
        }
    }
}


<#
.SYNOPSIS
    Get nearest number multiple.

.DESCRIPTION
    Converts input to a nearest multiple of a specified value.

.PARAMETER InputObject
    Input floating point number. Can pass multiple values via the pipeline.

.PARAMETER DoubleValue
    Return Double values nearest to multiples of this floating point number.

.PARAMETER IntegerValue
    Return Int32 values nearest to multiples of this integer.

.INPUTS
    Double

.OUTPUTS
    Double / Int32
#>
function Get-NearestMultiple {
    [CmdletBinding(DefaultParameterSetName = 'Floating')]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [double]$InputObject,

        [Parameter(Mandatory, Position = 0, ParameterSetName = 'Floating')]
        [double]$DoubleValue,

        [Parameter(ParameterSetName = 'Integer')]
        [Alias('Int')]
        [int]$IntegerValue
    )
    process {
        if ($PSCmdlet.ParameterSetName -eq 'Floating') {
            [System.Math]::Round($InputObject / $DoubleValue) * $DoubleValue
        } else {
            [int]($InputObject / $IntegerValue) * $IntegerValue
        }
    }
}


Export-ModuleMember -Function *-*
