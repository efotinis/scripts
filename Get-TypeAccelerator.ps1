<#
.SYNOPSIS
    Show type accelerators.

.DESCRIPTION
    Lists the current type accelerators.

.PARAMETER Name
    Pattern to filter accelerator name. Default is all ("*").

.PARAMETER TypeName
    Pattern to filter accelerator types full name.

.INPUTS
    None

.OUTPUTS
    PSCustomObject

.LINK
    https://stackoverflow.com/questions/1145312/where-can-i-find-a-list-of-powershell-net-type-accelerators
#>
[CmdletBinding(DefaultParameterSetName = 'Name')]
param(
    [Parameter(Position = 0, ParameterSetName = 'Name')]
    [SupportsWildcards()]
    [string]$Name = '*',

    [Parameter(ParameterSetName = 'TypeName')]
    [SupportsWildcards()]
    [string]$TypeName
)

# Convert dictionary entry to custom object.
filter Item {
    [PSCustomObject]@{
        Accelerator = $_.Key
        Type = $_.Value
    }
}

# Construct filter based on script paramset.
switch ($PSCmdlet.ParameterSetName) {
    'Name' {
        filter Match { if ($_.Accelerator -like $Name) { $_ } }
    }
    'TypeName' {
        filter Match { if ($_.Type.FullName -like $TypeName) { $_ } }
    }
}

$dict = [psobject].Assembly.GetType("System.Management.Automation.TypeAccelerators")::Get
$dict.GetEnumerator() | Item | Match
