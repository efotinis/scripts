<#
Link/copy pipelined filesystem items in random order with number prefix.
Unless copied, files produce hardlinks and directories junctions.

Can be used to access files in random order (e.g. media, documents).
The generated files can be either deleted (without affecting the originals)
or bookmarked in order to continue from that point at a later time.

WARNING:
While deleting hardlinks and junctions does not affect the originals,
the following will:
- editing hardlinks
- editing/deleting files in junctions
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    # Input file.
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [SupportsWildcards()]
    [Alias('PSPath', 'FullName')]
    [string[]]
    $InputObject,

    # Target directory. Will be created if needed.
    [Parameter(Mandatory)]
    [string]
    $Destination,

    # Copy items instead of creating hardlinks/junctions.
    [switch]
    $Copy
)

begin {
    Set-StrictMode -Version Latest
    $items = [System.Collections.ArrayList]@()

    function ProcessItem ($SrcPath, $NewPath, $IsDir, $Copy, $Info) {
        if ($Copy) {
            if ($IsDir) {
                Copy-Item -LiteralPath $SrcPath -Destination $NewPath -PassThru -Recurse
                $Info.bytesCopied += GetDirSize $SrcPath
            } else {
                Copy-Item -LiteralPath $SrcPath -Destination $NewPath -PassThru
                $Info.bytesCopied += (Get-Item -LiteralPath $SrcPath).Length
            }
        } else {
            # NOTE: New-Item's '-Value' is incorrectly treated as a wildcard and must be escaped.
            # See: https://github.com/PowerShell/PowerShell/issues/6232 (opened Feb 24, 2018)
            $SrcPath = $SrcPath.Replace('[','`[').Replace(']','`]')
            if ($IsDir) {
                New-Item -Type Junction -Path $NewPath -Value $SrcPath
            } else {
                New-Item -Type HardLink -Path $NewPath -Value $SrcPath
            }
        }
    }

    function GetDirSize ($Path) {
        Get-ChildItem -LiteralPath $Path -Recurse -Force |
            Measure-Item -Sum Length |
            Select-Object -ExpandProperty Sum
    }

}
process {
    [void]$items.AddRange(($InputObject | Get-Item))
}
end {
    # Create destination directory.
    <#
    # NOTE: '-Force' prevents error if directory already exists.
    #   However, it fails with root paths.
    $dest = New-Item -Type Directory -Path $Destination -Force
    if (-not $dest) {
        return
    }
    #>
    $dest = Get-Item -LiteralPath $Destination -ErrorAction Ignore
    if ($dest -and -not $dest.PSIsContainer) {
        Write-Error "destination path is a file: $Destination"
        return
    }
    if (-not $dest) {
        $dest = New-Item -Type Directory -Path $Destination
        if (-not $dest) {
            return
        }
    }

    if ($items.Count -eq 0) {
        Write-Error "No input items."
        return
    }

    # Shuffle items.
    $items = $items | Get-Random -Count $items.Count

    $indexFormat = 'D' + ([string]$items.Count).Length
    $index = 1
    $itemsOK, $itemsFailed = 0, 0

    $info = @{ bytesCopied=0 }
    $timer = [System.Diagnostics.Stopwatch]::StartNew()

    foreach ($item in $items) {
        $newName = $index.ToString($indexFormat) + '. ' + $item.Name
        $newPath = Join-Path $dest $newName
        if (ProcessItem $item.FullName $newPath $item.PSIsContainer $Copy $info) {
            ++$itemsOK
        } else {
            ++$itemsFailed
        }
        ++$index
    }

    $timer.Stop()
    $sec = $timer.Elapsed.TotalSeconds
    $speed = if ($sec) { $info.bytesCopied / $sec } else { 0 }

    Write-Host "items OK/failed: $itemsOK/$itemsFailed"
    if ($Copy) {
        Write-Host "speed: $(ConvertTo-NiceSize $speed)/s"
    }
}
