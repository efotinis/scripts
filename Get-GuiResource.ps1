<#
.SYNOPSIS
    Get process USER and GDI handle count.

.DESCRIPTION
    Gets current and peak USER and GDI handle counts of processes.
    Returns process objects with these additional members:
        - UserCount
        - UserPeak
        - GdiCount
        - GdiPeak

.PARAMETER InputObject
    Process ID. Can pass multiple values via the pipeline. If a process object
    is passed, it will be reused as output.

.INPUTS
    Process IDs or objects.

.OUTPUTS
    Process objects.

.NOTES
    References:
        - https://superuser.com/a/1535077
            "Echo GDI Object Count to Command Line or File"
        - https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguiresources
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('Id')]
    [int]$InputObject
)
begin {
    Add-Type -name NativeMethods -namespace Win32 -MemberDefinition @'
        [DllImport("User32.dll")]
        public static extern int GetGuiResources(IntPtr hProcess, int uiFlags);
'@

    $GR_GDIOBJECTS = 0
    $GR_USEROBJECTS = 1
    $GR_GDIOBJECTS_PEAK = 2  # Win 7 or Server 2008 R2 and later
    $GR_USEROBJECTS_PEAK = 4  # Win 7 or Server 2008 R2 and later

    function GetCount ($Handle, $Flag) {
        [Win32.NativeMethods]::GetGuiResources($Handle, $Flag)
    }
}
process {
    $p = if ($_ -is [System.Diagnostics.Process]) {
        # NOTE: Not much of a speed optimization, but it ensures that
        # the NoteProperty members are added to the input objects.
        $_
    } else {
        Get-Process -Id $InputObject
    }
    try {
        Add-Member -PassThru -InputObject $p -NotePropertyMembers @{
            UserCount = GetCount $p.Handle $GR_USEROBJECTS
            UserPeak = GetCount $p.Handle $GR_USEROBJECTS_PEAK
            GdiCount = GetCount $p.Handle $GR_GDIOBJECTS
            GdiPeak = GetCount $p.Handle $GR_GDIOBJECTS_PEAK
        }
    } catch {
        Write-Error "Could not GUI resources of process $($p.Name) with ID $($p.Id)"
    }
}
