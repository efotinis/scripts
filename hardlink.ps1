[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [IO.FileInfo]$File,
    
    [Parameter(Mandatory)]
    [string]$Destination
)
begin {
    if (-not (Test-Path -LiteralPath $Destination -Type Container)) {
        $outDir = New-Item -Path $Destination -Type Directory
    } else {
        $outDir = Get-Item -LiteralPath $Destination
    }
    function EscapeBrackets ([string]$s) {
        $s -replace '([[\]])','`$1'
    }
}
process {
    if (-not $outDir) {
        exit
    }
    $newPath = Join-Path $Destination $File.Name
    #$File | New-Item -Type HardLink -Path $newPath
    New-Item -Type HardLink -Path $newPath -Value (EscapeBrackets $File.FullName)
}
