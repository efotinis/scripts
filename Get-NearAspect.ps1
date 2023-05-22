<#
.SYNOPSIS
    Convert dimensions to look like common ratios.

.DESCRIPTION
    Simplies a width/height pair by selecting the denominator of a nearest common aspect ratio. This allows for quick comparison of slightly-off aspects. For example, a width:height of 740x540 yeilds a result of 4.11:3, making it obvious that the input is somewhere near 4:3.

    If the specfied width is less than the height, a portrait orientation of is assumed and the common ratios are used as such. For example 1080x1920 is returned as 9:16.

.PARAMETER Width
    Input width. Can use the pipeline to pass one or objects with this property.

.PARAMETER Height
    Input height. Can use the pipeline to pass one or objects with this property.

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

    if ($CommonRatio -is [string]) {
        $CommonRatio = $CommonRatio -split '\s+'
    }

    # Simple class specifying a ratio and denominator.
    class Aspect {
        [double]$Ratio
        [int]$Denominator
        Aspect ([double]$Rat, [int]$Den) {
            $this.Ratio = $Rat
            $this.Denominator = $Den
        }
    }

    # Convert piped aspect objects to account for boundaries between
    # adjucent ratios. Output objects are in sorted ratio order.
    function AdjustThresholds {
        $a = $input | Sort-Object -Property Ratio
        for ($i = 0; $i -lt $a.Count - 1; ++$i) {
            [Aspect]::new(
                # TODO: maybe use geometric mean instead?
                ($a[$i].Ratio + $a[$i+1].Ratio) / 2,
                $a[$i].Denominator
            )
        }
        [Aspect]::new(
            [double]::MaxValue,
            # NOTE: If 16:9 is the last ratio, setting the final denominator
            # to 1 causes 16:9 resolutions to be output as 1.(7):1.
            # It's better to either:
            #   - set it to the denominator of the last ratio (as done here)
            #   - set a custom one
            #   - use a threshold to extend the range of the last ratio
            #     above its value and *then* default to 1
            $a[-1].Denominator
        )
    }

    # Convert 'W:H' strings to Aspect objects.
    filter ParseAspect {
        if ($_ -notmatch '^\d+:\d+$') {
            throw "Aspect value does not match 'W:H': $Value"
        }
        $x, $y = $_ -split ':',2
        [Aspect]::new($x / $y, $y)
    }

    $LIMITS = $CommonRatio | ParseAspect | AdjustThresholds

    # Select best denominator for a ratio, i.e. the one in $LIMITS
    # that does not exceed its own ratio property.
    function GetBestDenominator ([double]$Ratio) {
        foreach ($a in $LIMITS) {
            if ($Ratio -le $a.Ratio) {
                return $a.Denominator
            }
        }
        throw 'Invalid denominator limits data.'
    }

}
process {
    $isPortrait = $Width -lt $Height
    if ($isPortrait) {
        $Width, $Height = $Height, $Width
    }

    $ratio = $Width / $Height
    $den = GetBestDenominator $ratio
    $num = [System.Math]::Round($ratio * $den, $Decimals)

    $s = if ($isPortrait) {
        "${den}:${num}"
    } else {
        "${num}:${den}"
    }

    Write-Output $s
}
