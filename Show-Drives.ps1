[CmdletBinding()]
param(
    [switch]$All  # include non-ready
)

Set-StrictMode -Version Latest

Add-Type -TypeDefinition @"
    using uint64 = System.UInt64;
    public struct DiskDrive {
        public string Letter;
        public string Label;
        public string Type;
        public string Format;
        public bool Ready;
        public uint64 Size;
        public uint64 Free;
        public uint64 UserFree;
        public double FreePercentage { get { return Size != 0 ? 100.0*Free/Size : 0; } }
        public double UserFreePercentage { get { return Size != 0 ? 100.0*UserFree/Size : 0; } }
        public DiskDrive(string letter, string label, string type, string format,
            bool ready, uint64 size, uint64 free, uint64 userFree)
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
