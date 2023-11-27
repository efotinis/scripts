<#
.SYNOPSIS
    Make objects from values.

.DESCRIPTION
    Creates a custom object using the specified property names and values. Missing values are set to the default, while extra ones generate a warning and are ignored.

.PARAMETER Property
    Output object property names.

.PARAMETER InputObject
    Output object property values. By default, this is an object array. It can be passed via the pipeline, but in that case it must be wrapped in a 1-element array (',@(...)').
    
    See also TabText.

.PARAMETER TabText
    Change input type to a tab-separated-value string.

.PARAMETER Default
    Value to use for missing items. Default is $null.

.INPUTS
    object[]
    string

.OUTPUTS
    PSCustomObject
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [string[]]$Property,
    
    [Parameter(Mandatory, ValueFromPipeline)]
    $InputObject,
    
    [switch]$TabText,
    
    $Default = $null
)
process {
    if ($TabText) {
        $InputObject = $InputObject -split "`t"
    }
    $i = 0
    $d = [ordered]@{}
    foreach ($s in $Property) {
        $d[$s] = if ($i -lt $InputObject.Count) {
            $InputObject[$i]
        } else {
            $Default
        }
        ++$i
    }
    $extra = $InputObject.Count - $Property.Count
    if ($extra -gt 0) {
        Write-Warning "Ignored $extra extra item(s) in: $InputObject"
    }
    New-Object -TypeName PSObject -Property $d
}
