<#
.SYNOPSIS
    Get drive information.

.DESCRIPTION
    Returns information about existing drives. Returned properties are:
        - Name      Assigned letter with colon, e.g. "C:".
        - Label     Drive label.
        - Type      Drive type (System.IO.DriveType enum).
        - Format    Filesystem format.
        - Ready     Boolean indicating that drive contains media.
        - Size      Total capacity in bytes.
        - Free      Total free bytes.
        - UserFree  Free bytes available to current user (quota).
        - FreePercentage            Total free perecentage (0-100; float).
        - UserFreeFreePercentage    User free perecentage (0-100; float).

.PARAMETER DriveType
    Return only drives of the specified type. Can specify one or more System.IO.DriveType enum values. If omitted, returns drives of all types.

.PARAMETER Label
    Return only drives with a matching label. Supports wildcards. Defaults to "*".

.PARAMETER IncludeNonReady
    Include drives like optical drives without media. Introduces a slight delay.

.INPUTS
    None

.OUTPUTS
    DiskDrive objects.

#>
[CmdletBinding()]
param(
    [System.IO.DriveType[]]$DriveType,

    [SupportsWildcards()]
    [string]$Label = '*',

    [switch]$IncludeNonReady
)

Set-StrictMode -Version Latest

Add-Type -TypeDefinition @"
    using int64 = System.Int64;
    public struct DiskDrive {
        public string Name;
        public string Label;
        public System.IO.DriveType Type;
        public string Format;
        public bool Ready;
        public int64 Size;
        public int64 Free;
        public int64 UserFree;
        public double FreePercentage { get { return Size != 0 ? 100.0*Free/Size : 0; } }
        public double UserFreePercentage { get { return Size != 0 ? 100.0*UserFree/Size : 0; } }
        public DiskDrive(string name, string label, System.IO.DriveType type, string format,
            bool ready, int64 size, int64 free, int64 userFree)
        {
            Name = name;
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


[System.IO.DriveInfo]::GetDrives() |
    Where-Object { $IncludeNonReady -or $_.IsReady } |
    Where-Object { $null -eq $DriveType -or $_.DriveType -in $DriveType } |
    Where-Object { $_.VolumeLabel -like $Label } |
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
