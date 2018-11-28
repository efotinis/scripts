<#
.SYNOPSIS
    Calculate statistics of objects or properties in the pipeline.

.DESCRIPTION
    Similar to Measure-Object, this script accepts objects from the pipeline and
    calculates various statistical values, including mean (average), variance, and
    standard deviation (stdev).

.PARAMETER InputObject
    The object to be measured. Note that, just like Measure-Object, collections are
    treated as a single object, unless they are passed through the pipeline.

.PARAMETER Property
    An array of property names for which to calculate statistics. If omitted, the
    whole object is used. When multiple properties are specified, a separate result
    is returned for each one. The object/properties must be convertible to double.

.PARAMETER Sample
    Set if the input represents a portion of the measured values. By default, it is
    assumed that the input represents the entirety of data (population).
#>
[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string[]]$Property,
    
    [Parameter(ValueFromPipeline=$True)]
    [PSObject]$InputObject,

    [Parameter()]
    [switch]$Sample
)
begin {
    Set-StrictMode -Version Latest

    class Info {
        [int]$Count = 0
        [double]$Sum = 0.0
        [double]$SumSq = 0.0
        [object]$Property = $null
        
        [void] AddValue ([double]$Value) {
            $This.Count += 1
            $This.Sum += $value
            $This.SumSq += $value * $value
        }
        
        [object] GetResult ([bool]$Sample) {
            $Denominator = if ($Sample) { $This.Count - 1 } else { $This.Count }
            $Variance = ($This.SumSq - ($This.Sum * $This.Sum) / $This.Count) / $Denominator
            if ($This.Count -gt 0) {
                return [PsCustomObject]@{
                    Sample=$Sample
                    Count=$This.Count
                    Sum=$This.Sum
                    SumSq=$This.SumSq
                    Mean=$This.Sum / $This.Count
                    Variance=$Variance
                    Stdev=[Math]::Sqrt($Variance)
                    Property=$This.Property
                }
            }
            throw ('no input object contained property "{0}"' -f $This.Property)
        }
    }
    
    class ObjectInfo : Info {

        [void] Add ($Object) {
            try {
                [double]$value = $Object
                $This.AddValue($value)
            }
            catch [InvalidCastException] {
                Write-Error 'cannot convert object to [double]'
            }
        }

    }
    
    class PropertyInfo : Info {

        PropertyInfo ([string]$Name) {
            $This.Property = $Name
        }

        [void] Add ($Object) {
            try {
                if (Get-Member $This.Property -InputObject $Object) {
                    [double]$value = $Object.($This.Property)
                    $This.AddValue($value)
                }
            }
            catch [InvalidCastException] {
                Write-Error 'cannot convert property to [double]'
            }
        }
    }

    $data = [System.Collections.Generic.List[Info]]::new()
    if ($Property -eq $null) {
        $data.Add([ObjectInfo]::new())
    }
    else {
        $h = [System.Collections.Generic.HashSet[string]]::new()
        foreach ($s in $Property) {
            if (!$h.Contains($s)) {
                $data.Add([PropertyInfo]::new($s))
                [void]$h.Add($s)
            }
        }
    }
}
process {
    foreach ($info in $data) {
        #$info.Add($_)
        $info.Add($InputObject)
    }
}
end {
    foreach ($info in $data) {
        try {
            $info.GetResult($Sample)
        }
        catch {
            Write-Error $_
        }
    }
}
