#requires -Modules PipelineUtil

<#
.SYNOPSIS
    Calculate statistics.

.DESCRIPTION
    Similar to Measure-Object, this script accepts objects from the pipeline
    and returns an object containing all the following statistical values:

        - Count: number of items
        - Sum: sum of values
        - SumSq: sum of squares of values
        - Mean: average
        - Variance: variance
        - Stdev: standard deviation

.PARAMETER InputObject
    The object to be measured. Note the collections must be passed via the
    pipeline in order to be treated as mulitple items.

.PARAMETER Property
    The property name of the object to use or a scriptblock to calculate a
    value using the current object as its first parameter. The resulting values
    must be convertible to double. If omitted, the whole object is used as-is.

    Multiple properties can be specified, in which case a separate result
    object is returned for each.

.PARAMETER Sample
    Set if the input represents a portion of the measured values. By default,
    it is assumed that the input represents the entirety of data (population).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    $InputObject,

    [Parameter(Mandatory, Position = 0)]
    [object[]]$Property = { $_ },

    [switch]$Sample
)
begin {
    Set-StrictMode -Version Latest

    class Counter {
    
        [object]$Property
        [bool]$Sample
        [int]$Count = 0
        [double]$Sum = 0.0
        [double]$SumSq = 0.0
        [bool]$NullsFound = $false
        [bool]$NonDoublesFound = $false
        
        Counter ($Property, [bool]$Sample) {
            $this.Property = $Property
            $this.Sample = $Sample
        }

        [void] Add ($Object) {
            $value = Get-ObjectValue -Prop $this.Property -Inp $Object
            if ($null -eq $value) {
                $this.NullsFound = $true
                return
            }
            try {
                $value = [double]$value
            } catch [InvalidCastException] {
                $this.NonDoublesFound = $true
                return
            }
            $this.Count += 1
            $this.Sum += $value
            $this.SumSq += $value * $value
        }
        
        [double] GetVariance () {
            $numerator = if ($this.Count) {
                $this.SumSq - ($this.Sum * $this.Sum) / $this.Count
            } else {
                0
            }
            $denominator = if ($this.Sample) {
                $this.Count - 1
            } else {
                $this.Count
            }
            if ($denominator) {
                return $numerator / $denominator
            } else {
                return 0
            }
        }

        [object] GetResult () {
            if ($this.NullsFound) {
                Write-Warning "Property had null or missing: $($this.Property)"
            }
            if ($this.NonDoublesFound) {
                Write-Warning "Property had non-double values: $($this.Property)."
            }
            if ($this.Count -eq 0) {
                throw "No valid values for property: $($this.Property)"
            }
            $var = $this.GetVariance()
            return [PsCustomObject]@{
                Sample = $this.Sample
                Count = $this.Count
                Sum = $this.Sum
                SumSq = $this.SumSq
                Mean = $this.Sum / $this.Count
                Variance = $var
                Stdev = [Math]::Sqrt($var)
                Property = $this.Property
            }
        }
    }
    
    $counters = @()
    foreach ($prop in $Property) {
        $counters += [Counter]::new($prop, $Sample)
    }
}
process {
    foreach ($c in $counters) {
        $c.Add($InputObject)
    }
}
end {
    foreach ($c in $counters) {
        try {
            $c.GetResult()
        } catch [System.Management.Automation.RuntimeException] {
            Write-Error $_.Exception.Message
        }
    }
}
