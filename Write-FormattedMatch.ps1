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

.PARAMETER Color
    Hashtable with color values for different parts of the output. Available keys:
        - Text / TextCtx    Lines of text (matching/context).
        - Line / LineCtx    Lines numbers (matching/context).
        - Path              File path header.
        - Match / MatchBg   Substring matches (foreground/background).

    By default, the current foreground/background colors are used.

    $PSDefaultParameterValues can be used to set a global preference. See `help about_Preference_Variables` for details.

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

    [switch]$Compact,

    [hashtable]$Color = @{}
)
begin {
    function InitColor ($Type, $Default) {
        $n = $Color[$Type] -as [System.ConsoleColor]
        if ($null -eq $n) {
            $n = $Default
        }
        $Color[$Type] = $n
    }

    $fg = $Host.UI.RawUI.ForegroundColor
    $bg = $Host.UI.RawUI.BackgroundColor
    InitColor 'Text' $fg
    InitColor 'TextCtx' $fg
    InitColor 'Line' $fg
    InitColor 'LineCtx' $fg
    InitColor 'Path' $fg
    InitColor 'Match' $bg
    InitColor 'MatchBg' $fg

    function WriteMatchLine ($Text, $Index, $Length) {
        Write-Host -NoNew -Fore $Color['Text'] $Text.Substring(0, $Index)
        Write-Host -NoNew -Fore $Color['Match'] -Back $Color['MatchBg'] $Text.Substring($Index, $Length)
        Write-Host -NoNew -Fore $Color['Text'] $Text.Substring($Index + $Length)
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
        Write-Host -Fore $Color['Path'] ('----- ' + $path)
    }

    if ($InputObject.Context) {
        $n = $InputObject.LineNumber - $InputObject.Context.DisplayPreContext.Length
        $InputObject.Context.DisplayPreContext | % {
            Write-Host -NoNew -Fore $Color['LineCtx'] ((LineStr $n) + ' ')
            Write-Host -Fore $Color['TextCtx'] $_
            ++$n
        }
    }
    Write-Host -NoNew -Fore $Color['Line'] "$((LineStr $InputObject.LineNumber)) "
    WriteMatchLine $InputObject.Line $InputObject.Matches[0].Index $InputObject.Matches[0].Length
    Write-Host ''
    if ($InputObject.Context) {
        $n = $InputObject.LineNumber + 1
        $InputObject.Context.DisplayPostContext | % {
            Write-Host -NoNew -Fore $Color['LineCtx'] ((LineStr $n) + ' ')
            Write-Host -Fore $Color['TextCtx'] $_
            ++$n
        }
    }

}
end {
    if (-not $Compact) {
        Write-Host ''
    }
}
