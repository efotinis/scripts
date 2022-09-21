<#
.SYNOPSIS
    Delete shell items.

.DESCRIPTION
    Invokes the shell Delete operation for the specified filesystem items.
    If the Recycle Bin is used, the items are moved there silently. Otherwise
    the user is prompted to permanently delete them.

.PARAMETER InputObject
    Input filesystem item. Can pass multiple values via the pipeline.

.INPUTS
    Item paths.

.OUTPUTS
    None.

.NOTES
    Source:
        - https://social.technet.microsoft.com/Forums/en-US/ff39d018-9c38-4276-a4c9-3234f088c630
            "How can I delete "to recycle bin" in powershell instead of remove item ?"
            DakotaZinn -- Friday, January 17, 2020 8:44 PM
#>
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('FullName', 'PSPath')]
    [string]$InputObject
)
begin{
    $shell = New-Object -ComObject 'Shell.Application'
    $desktop = $shell.Namespace(0)
}
process{
    $item = Get-Item -LiteralPath $InputObject
    $desktop.ParseName($item.FullName).InvokeVerb('delete')
}
