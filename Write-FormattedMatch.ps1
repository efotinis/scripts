<#
.SYNOPSIS
    Output Select-String results with color.

.DESCRIPTION
    Writes MatchInfo objects to the host with special formatting and color.

.PARAMETER InputObject
    String matching object, as returned by Select-String. Can pass multiple items via the pipeline.

.PARAMETER PathDisplay
    Specify how to display file paths. One of:
        - FullPath  Show the full path (default).
        - NameOnly  Show only the file name (with extension).
        - Relative  Show the path relative to the current one.

.PARAMETER Compact
    Suppress empty lines separating files.

.INPUTS
    MatchInfo

.OUTPUTS
    None
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [Microsoft.PowerShell.Commands.MatchInfo]$InputObject,

    [ValidateSet('FullPath', 'NameOnly', 'Relative')]
    [string]$PathDisplay = 'FullPath',
    
    [switch]$Compact
)
begin {
    function WriteMatchLine ($Text, $Index, $Length) {
        Write-Host -NoNew -Fore White $Text.Substring(0, $Index)
        Write-Host -NoNew -Fore White -Back DarkGray $Text.Substring($Index, $Length)
        Write-Host -NoNew -Fore White $Text.Substring($Index + $Length)
    }
    
    function LineStr ([int]$Value) {
        $Value.ToString('D5')
    }

    $prevFile = ''
}
process {
    $path = switch ($PathDisplay) {
        'FullPath' { $InputObject.Path }
        'NameOnly' { Split-Path -Leaf -Path $InputObject.Path }
        'Relative' { Resolve-Path -Relative $InputObject.Path }
    }
    if ($prevFile -ne $InputObject.Path) {
        $prevFile = $InputObject.Path
        if (-not $Compact) {
            Write-Host ''
        }
        Write-Host -Fore Yellow ('----- ' + $path)
    }

    if ($InputObject.Context) {
        $n = $InputObject.LineNumber - $InputObject.Context.DisplayPreContext.Length
        $InputObject.Context.DisplayPreContext | % {
            Write-Host -NoNew -Fore DarkBlue ((LineStr $n) + ' ')
            Write-Host -Fore Gray $_
            ++$n
        }
    }
    Write-Host -NoNew -Fore Blue "$((LineStr $InputObject.LineNumber)) "
    WriteMatchLine $InputObject.Line $InputObject.Matches[0].Index $InputObject.Matches[0].Length
    Write-Host ''
    if ($InputObject.Context) {
        $n = $InputObject.LineNumber + 1
        $InputObject.Context.DisplayPostContext | % {
            Write-Host -NoNew -Fore DarkBlue ((LineStr $n) + ' ')
            Write-Host -Fore Gray $_
            ++$n
        }
    }

}
end {
    if (-not $Compact) {
        Write-Host ''
    }
}
