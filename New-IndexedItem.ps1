<#
.SYNOPSIS
    Create filesystem objects with numeric prefix from existing items.

.DESCRIPTION
    Generates new file and directory objects from existing items and inserts
    an increasing index as a name prefix.

.PARAMETER Path
    Input item path. Wildcards are supported. Can specify multiple items either
    as an array or via the pipeline.

.PARAMETER LiteralPath
    Input item path. Wildcards are ignored. Can specify multiple items either
    as an array or via the pipeline.

.PARAMETER Destination
    Output directory. Will be created if needed.

.PARAMETER Operation
    Method of new item creation. One of:

        - Copy:         Files and directories are copied.
        - Link:         Hardlinks are created for files and junctions for
                        directories.
        - SymbolicLink: Symbolic links of files and directories are created.
                        This operation requires elevation.

.PARAMETER StartIndex
    Initial prefix number of created items. Default is 1.

.PARAMETER Shuffle
    Randomize the order of new items.

.INPUTS
    Input item paths.

.OUTPUTS
    New filesystem objects.
#>
[CmdletBinding(SupportsShouldProcess, DefaultParameterSetName = 'Path')]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName, Position = 0, ParameterSetName = 'Path')]
    [SupportsWildcards()]
    [string[]]$Path,

    [Parameter(Mandatory, ValueFromPipelineByPropertyName, ParameterSetName = 'LiteralPath')]
    [SupportsWildcards()]
    [Alias('PSPath')]
    [string[]]$LiteralPath,

    [Parameter(Mandatory)]
    [string]$Destination,

    [Parameter(Mandatory)]
    [ValidateSet('Copy', 'Link', 'SymbolicLink')]
    [string]$Operation,

    [int]$StartIndex = 1,

    [switch]$Shuffle
)

begin {
    Set-StrictMode -Version Latest
    $items = [System.Collections.ArrayList]@()

    # Handle item and return new item object.
    function ProcessItem ($SrcPath, $NewPath, $IsDir) {
        if ($Operation -eq 'Copy') {
            if ($IsDir) {
                Copy-Item -LiteralPath $SrcPath -Destination $NewPath -Recurse
                if ($?) { Get-Item -LiteralPath $NewPath }
            } else {
                Copy-Item -LiteralPath $SrcPath -Destination $NewPath -PassThru
            }
        } else {
            if ($Operation -eq 'SymbolicLink') {
                $type = 'SymbolicLink'
            } elseif ($IsDir) {
                $type = 'Junction'
            } else {
                $type = 'HardLink'
            }
            # NOTE: New-Item's `-Value` is incorrectly treated as a wildcard,
            # so brackets must be backtick-escaped. See issue Feb 24, 2018:
            #   https://github.com/PowerShell/PowerShell/issues/6232
            $SrcPath = $SrcPath -replace '([[\]])','`$1'
            New-Item -Type $type -Path $NewPath -Value $SrcPath
        }
    }

}
process {
    $a = @(switch ($PSCmdlet.ParameterSetName) {
        'Path' { Get-Item -Path $Path }
        'LiteralPath' { Get-Item -LiteralPath $LiteralPath }
    })
    [void]$items.AddRange($a)
}
end {
    # NOTE: Test destination explicitly instead of using `New-Item -Force`,
    # to report error if it's file and to avoid failure if it's a root path.
    $dest = Get-Item -LiteralPath $Destination -ErrorAction Ignore
    if ($dest -and -not $dest.PSIsContainer) {
        Write-Error "Destination path is a file: $Destination"
        return
    }
    if (-not $dest) {
        $dest = New-Item -Type Directory -Path $Destination
        if (-not $dest) {
            return
        }
    }

    if ($Shuffle) {
        $items = $items | Get-Random -Count $items.Count
    }

    $indexFormat = 'D' + ([string]$items.Count).Length
    $index = $StartIndex

    foreach ($item in $items) {
        $newName = $index.ToString($indexFormat) + '. ' + $item.Name
        $newPath = Join-Path $dest $newName
        ProcessItem $item.FullName $newPath $item.PSIsContainer
        ++$index
    }
}
