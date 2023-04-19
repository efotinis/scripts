<#
.SYNOPSIS
    Get object type.

.DESCRIPTION
    Returns the type of NET and COM objects passed via the pipeline.

.PARAMETER Object
    Input object.

.PARAMETER TypeType
    Determines what kind of type info is returned. One of:

        - Object    TypeInfo object as returned by GetType (default).
        - Name      Type name string.
        - FullName  Type full name string.

    The full name of COM objects is the generic full name and the actual object name separated by a colon, e.g. "System.__ComObject:FolderItem2".

.INPUTS
    Object

.OUTPUTS
    TypeInfo / string

#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    $Object,

    [Parameter(Position = 0)]
    [ValidateSet('Name', 'FullName', 'Object')]
    [string]$TypeType = 'Name'
)
begin {

    Add-Type -AssemblyName Microsoft.VisualBasic

    function NetTypeName ($Object, [bool]$Full) {
        if ($Full) {
            Write-Output $Object.GetType().FullName
        } else {
            Write-Output $Object.GetType().Name
        }
    }

    function ComTypeName ($Object, [bool]$Full) {
        $comName = [Microsoft.VisualBasic.Information]::TypeName($Object)
        if ($Full) {
            Write-Output ($Object.GetType().FullName + ':' + $comName)
        } else {
            Write-Output $comName
        }
    }

}
process {

    if ($TypeType -eq 'Object') {
        Write-Output $Object.GetType()
    } elseif ($Object -is [System.__ComObject]) {
        ComTypeName $Object ($TypeType -eq 'FullName')
    } else {
        NetTypeName $Object ($TypeType -eq 'FullName')
    }

}
