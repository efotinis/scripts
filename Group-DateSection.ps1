<#
.SYNOPSIS
    Group by date section.

.DESCRIPTION
    Group objects by year, quarter or year/month. The date property can be
    specified by name or calculated using a scriptblock.
    
    By default, groups of all date sections between the minimum and maximum
    are generated in sorted order unless NoEmpty is set.

.PARAMETER InputObject
    Input objects. Must be passed via the pipeline.

.PARAMETER Section
    Date section to group objects by. Also determines the format of the Section
    output property. One of:

        - Year:     Example: "2023"
        - Quarter:  Example: "2023-Q1", "2023-Q4"
        - Month:    Example: "2023-01", "2023-12"

.PARAMETER Property
    The property to use as the date of the input objects. Its type can vary:
    
        - [string]:         Property name.
        - [scriptblock]:    Use to calculate date value. The input object is
                            made available inside the scriptblock as $_.
        - $null / omitted:  Assume input objects are DateTime objects.

.PARAMETER NoElement
    Do not include the input objects in the output as a Group property.

.PARAMETER NoEmpty
    Do not generate empty groups for date sections with no items. This also
    prevents the output from being automatically sorted by date section.

.INPUTS
    Objects.

.OUTPUTS
    Custom objects.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [object]$InputObject,
    
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('Year', 'Quarter', 'Month')]
    [string]$Section,
    
    [Parameter(Position = 1)]
    $Property,  # $null, string, or scriptblock
    
    [switch]$NoElement,
    
    [switch]$NoEmpty
)
begin {
    function MinMax ([object[]]$Value) {
        $m = $Value | measure -min -max
        $m.Minimum, $m.Maximum
    }
    if ($Property -is [scriptblock]) {
        function GetDateValue ($Obj) {
            $Property.InvokeWithContext(
                $null,
                [psvariable]::new('_', $Obj),
                $null
            )[0]
        }
    } elseif ($Property -is [string]) {
        function GetDateValue ($Obj) { $Obj.$Property }
    } else {
        function GetDateValue ($Obj) { $Obj }
    }
    $groups = @{}
    function GetGroup ([string]$Key) {
        if (-not $groups.ContainsKey($Key)) {
            $groups[$Key] = @{
                count = 0
                items = [System.Collections.ArrayList]::new()
            }
        }
        return $groups[$Key]
    }
    function Output ([string]$Key, $Group) {
        $o = [PSCustomObject]@{
            Section = $Key
            Count = $Group.count
        }
        if (-not $NoElement) {
            Add-Member -InputObject $o Group $Group.items
        }
        Write-Output $o
    }
}
process {
    $k = (GetDateValue $InputObject) | Get-DateSection -Type $Section
    $g = GetGroup $k
    $g.count += 1
    if (-not $NoElement) {
        [void]$g.items.Add($InputObject)
    }
}
end {
    if ($NoEmpty) {
        foreach ($e in $groups.GetEnumerator()) {
            Output $e.Key $e.Value
        }
    } else {
        $keys = @($groups.Keys)
        $min, $max = MinMax $keys
        Get-DateSectionRange $min $max | % {
            Output $_ (GetGroup $_)
        }
    }
}
