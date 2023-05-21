[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
    [int]$Width,

    [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
    [int]$Height,

    [ValidateRange(0, 10)]
    [int]$Decimals = 2
)
begin {

    function CommonRatios {
        #'4:3 5:4 3:2 16:10 16:9 17:9 21:9 32:9 1:1 4:1' -split '\s+' | % {
        '4:3 5:4 3:2 16:10 16:9' -split '\s+' | % {
            $w, $h = $_ -split ':',2
            [PSCustomObject]@{
                Width = $w
                Height = $h
                Ratio = $w / $h
            }
        }
    }

    function OrderedDenominatorUpperLimits {
        $a = CommonRatios | Sort-Object -Property Ratio
        for ($i = 0; $i -lt $a.Count - 1; ++$i) {
            [PSCustomObject]@{
                # TODO: maybe use geometric mean instead?
                Limit = ($a[$i].Ratio + $a[$i+1].Ratio) / 2
                Denominator = $a[$i].Height
            }
        }
        [PSCustomObject]@{
            Limit = [double]::MaxValue
            # NOTE: If 16:9 is the last ratio, setting the final denominator
            # to 1 causes 16:9 resolutions to be output as 1.(7):1.
            # It's better to either:
            #   - set it to the denominator of the last ratio (as done here)
            #   - set a custom one
            #   - use a threshold to extend the range of the last ratio
            #     above its value and *then* default to 1
            #Denominator = 1
            Denominator = $a[-1].Height
        }
    }

    $LIMITS = OrderedDenominatorUpperLimits

    function GetDenominator ([double]$Ratio) {
        foreach ($a in $LIMITS) {
            if ($Ratio -le $a.Limit) {
                return $a.Denominator
            }
        }
        throw 'Invalid denominator limits data.'
    }

    $MAX_DENOM_WIDTH = ($LIMITS | Measure-Object -Maximum -Property Denominator).Maximum.ToString().Length

    $OUT_WIDTH = ( 5 + # semi-arbitrary, assuming something like '12345.67:1'
        ($Decimals -gt 0) + # decimal point
        $Decimals +
        1 +  # colon
        $MAX_DENOM_WIDTH
    )


}
process {
    $ratio = $Width / $Height
    $den = GetDenominator $ratio
    $num = $ratio * $den
    #Write-Output "${num}:${den}"

    $num = [System.Math]::Round($num, $Decimals)
    $den = $den.ToString().PadRight($MAX_DENOM_WIDTH)
    $s = "${num}:${den}".PadLeft($OUT_WIDTH)
    Write-Output $s

    <#
    filter GroupDims {
        if ($_.Name -notmatch '(\d+), (\d+)') {
            Write-Error "Unexpected size: $($_.Name)"
        } else {
            [PSCustomObject]@{ Width = $Matches[1]; Height = $Matches[2]; }
        }
    }
    #>

}
