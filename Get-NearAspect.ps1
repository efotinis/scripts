<#
.SYNOPSIS
    Convert dimensions to look like common ratios.

.DESCRIPTION
    Simplies a width/height pair by selecting the denominator of a nearest common aspect ratio. This allows for quick comparison of slightly-off aspects. For example, a width:height of 740x540 yeilds a result of 4.11:3, making it obvious that the input is somewhere near 4:3.

    If the specfied width is less than the height, a portrait orientation of is assumed and the common ratios are used as such. For example 1080x1920 is returned as 9:16.

.PARAMETER Width
    Input width.

.PARAMETER Height
    Input height.

.PARAMETER Decimals
    Maximum number of numerator decimals. Default is 2.

.PARAMETER CommonRatio
    A list of ratios to use for reference. Can specify an array of 'width:height' strings or a single string concatenated with withspace. Default is '4:3 5:4 3:2 16:10 16:9'.

.INPUTS
    None.

.OUTPUTS
    String.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
    [int]$Width,

    [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
    [int]$Height,

    [ValidateRange(0, 10)]
    [int]$Decimals = 2,

    $CommonRatio = '4:3 5:4 3:2 16:10 16:9'
)
begin {

    function ParseRatios ($Value) {
        if ($Value -is [string]) {
            $Value = $Value -split '\s+'
        }
        foreach ($s in $Value) {
            $w, $h = $s -split ':',2
            [PSCustomObject]@{
                Width = $w
                Height = $h
                Ratio = $w / $h
            }
        }
    }

    function OrderedDenominatorUpperLimits {
        $a = ParseRatios $CommonRatio | Sort-Object -Property Ratio
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
    $isPortrait = $Width -lt $Height
    if ($isPortrait) {
        $Width, $Height = $Height, $Width
    }

    $ratio = $Width / $Height
    $den = GetDenominator $ratio
    $num = $ratio * $den

    $num = [System.Math]::Round($num, $Decimals)
    #$den = $den.ToString().PadRight($MAX_DENOM_WIDTH)
    #$s = "${num}:${den}".PadLeft($OUT_WIDTH)
    $s = if ($isPortrait) {
        "${den}:${num}"
    } else {
        "${num}:${den}"
    }

    Write-Output $s
}
