<#
.SYNOPSIS
    Get the actual data length of files.

.DESCRIPTION
    Get information about the actual data length of file. This may be different
    than the logical size in the case of compressed and sparse files.
    
    Returned objects have the following members:
        - Path (string): Full file path.
        - Logical (ulong): Logical size.
        - Physical (ulong): Physical size. Always less than or equal to Logical.
        - Delta (ulong): Difference between Logical and Physical. Non-negative.
        - IsSparse (bool): File is sparse.
        - IsCompressed (bool): File is compressed.
        - IsComplete (bool): File is either non-sparse or has no missing ranges.
    
    Container objects are not valid input and will generate errors.
    
    The default table output format contains a Flags columns for boolean
    properties: 'c' = IsCompressed, 'p' = IsSparse, 'k' = IsComplete

        This is 

.PARAMETER InputObject
    Path of file. Can pass multiple items via the pipeline.

.INPUTS
    File path(s).

.OUTPUTS
    Length information object(s).
#>

<#
TODO:
    - investigate what happens when a file is both sparse and compressed
    - option AsFileObject: return FileInfo with extra properties instead of custom object
#>

param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('FullName')]
    [string]$InputObject
)
begin {
    if (-not ('Win32Functions.ExtendedFileInfo' -as [type])) {
        Add-Type -Type @'
using System;
using System.Runtime.InteropServices;
using System.ComponentModel;

namespace Win32Functions {

    public class ExtendedFileInfo {

        [DllImport("kernel32.dll", SetLastError=true, EntryPoint="GetCompressedFileSize")]
        static extern uint GetCompressedFileSizeAPI(string lpFileName, out uint lpFileSizeHigh);

        public static ulong GetCompressedFileSize(string filename) {
            uint high;
            uint low = GetCompressedFileSizeAPI(filename, out high);
            int error = Marshal.GetLastWin32Error();
            if (high == 0 && low == 0xffffffff && error != 0)
                throw new Win32Exception(error);
            else
                return ((ulong)high << 32) + low;
        }
    }

}

public struct FileDataLength {
    public string Path;
    public ulong Logical;
    public ulong Physical;
    public ulong Delta { get { return Logical - Physical; } }
    public bool IsSparse;
    public bool IsCompressed;
    public bool IsComplete { get { return !IsSparse || Delta == 0; } }
    public FileDataLength (string path, ulong logical, ulong physical, bool isSparse, bool isCompressed) {
        Path = path;
        Logical = logical;
        Physical = physical;
        IsSparse = isSparse;
        IsCompressed = isCompressed;
    }
};
'@
    }
    
    function HasAttr ([System.IO.FileInfo]$File, [System.IO.FileAttributes]$Attr) {
        return ($File.Attributes -band $Attr) -ne 0
    }
}
process {
    $info = Get-Item -LiteralPath $InputObject
    if ($info.PSIsContainer) {
        Write-Error "Item is a container: $($info.FullName)"
    } else {
        [FileDataLength]::new(
            $info.FullName,
            $info.Length,
            [Win32Functions.ExtendedFileInfo]::GetCompressedFileSize($info.FullName),
            (HasAttr $info SparseFile),
            (HasAttr $info Compressed)
        )
    }
}
