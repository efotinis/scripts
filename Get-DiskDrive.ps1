<#
.SYNOPSIS
    Get drive information.

.DESCRIPTION
    Returns information about existing drives. Returned properties are:
        - Letter    Assigned letter with colon, e.g. "C:".
        - Label     Drive label.
        - Type      Drive type (System.IO.DriveType enum).
        - Format    Filesystem format.
        - Ready     Boolean indicating that drive contains media.
        - Size      Total capacity in bytes.
        - Free      Total free bytes.
        - UserFree  Free bytes available to current user (quota).
        - FreePercentage            Total free perecentage (0-100; float).
        - UserFreeFreePercentage    User free perecentage (0-100; float).

.PARAMETER All
    Include drives that are not ready (e.g. optical drives without media). Querying information about such drives introduces a slight delay, so they are excluded by default.

.INPUTS
    None

.OUTPUTS
    DiskDrive objects.

#>
[CmdletBinding()]
param(
    [switch]$All  # include non-ready
)

Set-StrictMode -Version Latest

Add-Type -TypeDefinition @"
    using int64 = System.Int64;
    public struct DiskDrive {
        public string Letter;
        public string Label;
        public System.IO.DriveType Type;
        public string Format;
        public bool Ready;
        public int64 Size;
        public int64 Free;
        public int64 UserFree;
        public double FreePercentage { get { return Size != 0 ? 100.0*Free/Size : 0; } }
        public double UserFreePercentage { get { return Size != 0 ? 100.0*UserFree/Size : 0; } }
        public DiskDrive(string letter, string label, System.IO.DriveType type, string format,
            bool ready, int64 size, int64 free, int64 userFree)
        {
            Letter = letter;
            Label = label;
            Type = type;
            Format = format;
            Ready = ready;
            Size = size;
            Free = free;
            UserFree = userFree;
        }
    }
"@

Update-FormatData $Env:SyncMain\util\fmt.ps1xml


[System.IO.DriveInfo]::GetDrives() |
    Where-Object { $All -or $_.IsReady } |
    Foreach-Object {
        [DiskDrive]::new(
            $_.Name.Substring(0, 2),
            $_.VolumeLabel,
            $_.DriveType,
            $_.DriveFormat,
            $_.IsReady,
            $_.TotalSize,
            $_.TotalFreeSpace,
            $_.AvailableFreeSpace
        )
    }
