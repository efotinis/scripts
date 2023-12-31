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

.PARAMETER Name
    One or more letters specifying which drives to return. If omitted, all drives are returned.

.PARAMETER Label
    Return only drives with a matching label. Supports wildcards.

    When no matching label is found, an error is generated, but only if no wildcards were used. This matches the behavior of standard cmdlets, like Get-Item.

.PARAMETER DriveType
    Return only drives of the specified type. Can specify one or more System.IO.DriveType enum values. If omitted, returns drives of all types.

.PARAMETER IncludeNonReady
    Include devices like optical drives without media. Introduces a slight delay.

.INPUTS
    None

.OUTPUTS
    DiskDrive objects.

#>
[CmdletBinding(DefaultParameterSetName = 'Name')]
param(
    [Parameter(ParameterSetName = 'Name', Position = 0)]
    [ValidatePattern('[A-Z]')]
    [char[]]$Name,

    [Parameter(ParameterSetName = 'Label')]
    [SupportsWildcards()]
    [string]$Label,

    [Alias('Type')]
    [System.IO.DriveType[]]$DriveType,

    [switch]$IncludeNonReady
)

Set-StrictMode -Version Latest

Add-Type -TypeDefinition @"
    using int64 = System.Int64;
    public struct DiskDrive {
        public string FullName;
        public string Label;
        public System.IO.DriveType Type;
        public string Format;
        public bool Ready;
        public int64 Size;
        public int64 Free;
        public int64 UserFree;
        public double FreePercentage { get { return Size != 0 ? 100.0*Free/Size : 0; } }
        public double UserFreePercentage { get { return Size != 0 ? 100.0*UserFree/Size : 0; } }
        public DiskDrive(string path, string label, System.IO.DriveType type, string format,
            bool ready, int64 size, int64 free, int64 userFree)
        {
            FullName = path;
            Label = label;
            Type = type;
            Format = format;
            Ready = ready;
            Size = size;
            Free = free;
            UserFree = userFree;
        }
        public string Name {
            get { return FullName.Substring(0, 2); }
        }
        public string LiteralPath {
            get { return FullName; }
        }
    }
"@


switch ($PSCmdlet.ParameterSetName) {
    'Name' {
        filter SelectItems {
            if (-not $Name -or $_.Name[0] -in $Name) {
                $_
            }
        }
    }
    'Label' {
        filter SelectItems {
            if ($_.VolumeLabel -like $Label) {
                $_
            }
        }
    }
}


filter Output {
    [DiskDrive]::new(
        $_.Name,
        $_.VolumeLabel,
        $_.DriveType,
        $_.DriveFormat,
        $_.IsReady,
        $_.TotalSize,
        $_.TotalFreeSpace,
        $_.AvailableFreeSpace
    )
}


$MatchedItems = $null

[System.IO.DriveInfo]::GetDrives() |
    Where-Object { $IncludeNonReady -or $_.IsReady } |
    Where-Object { $null -eq $DriveType -or $_.DriveType -in $DriveType } |
    SelectItems |
    Tee-Object -Variable MatchedItems |
    Output

if ($PSCmdlet.ParameterSetName -eq 'Label' -and
    -not [WildcardPattern]::ContainsWildcardCharacters($Label) -and
    -not $MatchedItems)
{
    Write-Error "No drive with label: $Label"
}
