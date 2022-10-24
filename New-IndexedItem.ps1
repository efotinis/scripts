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

.PARAMETER Copy
    Copy input items. If omitted, file hardlinks and directory junctions are
    created.

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

    [switch]$Copy,

    [switch]$Shuffle
)

begin {
    Set-StrictMode -Version Latest
    $items = [System.Collections.ArrayList]@()

    function ProcessItem ($SrcPath, $NewPath, $IsDir, $Copy) {
        if ($Copy) {
            if ($IsDir) {
                Copy-Item -LiteralPath $SrcPath -Destination $NewPath -PassThru -Recurse
            } else {
                Copy-Item -LiteralPath $SrcPath -Destination $NewPath -PassThru
            }
        } else {
            # NOTE: New-Item's '-Value' is incorrectly treated as a wildcard
            # and must be escaped. See issue open on Feb 24, 2018:
            #   https://github.com/PowerShell/PowerShell/issues/6232
            $SrcPath = $SrcPath.Replace('[','`[').Replace(']','`]')
            if ($IsDir) {
                New-Item -Type Junction -Path $NewPath -Value $SrcPath
            } else {
                New-Item -Type HardLink -Path $NewPath -Value $SrcPath
            }
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
    $index = 1

    foreach ($item in $items) {
        $newName = $index.ToString($indexFormat) + '. ' + $item.Name
        $newPath = Join-Path $dest $newName
        ProcessItem $item.FullName $newPath $item.PSIsContainer $Copy
        ++$index
    }
}
