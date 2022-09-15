Set-StrictMode -Version Latest


$script:Options = @{

    # Part of current path to display:
    #   - 'Full': Whole path.
    #   - 'Tail': Last component.
    #   - 'None': Nothing.
    PathDisplay = 'Tail'

    # Replace HOME path prefix with ":~"
    ReplaceHome = $true

}


$script:Components = @()


# TODO: Reimplement special color codes of original design?
#   ('i': swap fg/bg, '*','/*','*/*': toggle fg/bg intensity)
#
# TODO: Handle hosts other than ConsoleHost.
#


function global:prompt {
    foreach ($c in $script:Components) {
        $fg, $bg = global:Get-ColorAttribute $c.Color
        $args = @{
            Object = & $c.Expression
            NoNewLine = $true
        }
        if ($null -ne $fg) {
            $args.ForegroundColor = $fg
        }
        if ($null -ne $bg) {
            $args.BackgroundColor = $bg
        }
        Write-Host @args
    }
    # HACK: A non-empty value must be ouput, otherwise Write-Host is buffered,
    # no output is produced and the default, fallback prompt ("PS>") is used
    # instead.
    Write-Output ' '
}


function Set-ModPromptOption {
    [CmdletBinding()]
    param(
        [ValidateSet('Full', 'Tail', 'None')]
        [string]$PathDisplay,

        [bool]$ReplaceHome
    )
    if ($PSBoundParameters.ContainsKey('PathDisplay')) {
        $script:Options.PathDisplay = $PathDisplay
    }
    if ($PSBoundParameters.ContainsKey('ReplaceHome')) {
        $script:Options.ReplaceHome = $ReplaceHome
    }
}


function Get-ModPromptOption {
    [CmdletBinding()]
    param()
    $script:Options.Clone()
}



<#
# Get index of component with matching Id, or -1 if not found.
function GetComponentIndex ([string]$Id) {
    for (
        $n = $script:Components.Count - 1;
        $n -gt 0 -and $script:Components.Id -ne $Id;
        --$n
    ) {
    }
    return $n
}
#>


function Add-ModPromptItem {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Id,

        [Parameter(Mandatory)]
        [string]$Color,

        [Parameter(Mandatory)]
        [scriptblock]$Expression
    )
    $script:Components += [PSCustomObject]@{
        Id = $Id
        Color = $Color
        Expression = $Expression
    }
}


Add-ModPromptItem -Id 'Elevation' -Color 'w+/r' -Expression {
    if (IsAdmin) {
        'ADMIN:'
    } else {
        ''
    }
}


Add-ModPromptItem -Id 'JobCount' -Color 'w+/b' -Expression {
    $a = @(Get-Job)
    if ($a.Count -gt 0) {
        "{0}j:" -f $a.Count
    } else {
        ''
    }
}


Add-ModPromptItem -Id 'Path' -Color 'w+/n+' -Expression {
    $s = ''
    if ($script:Options.PathDisplay -ne 'None') {
        # FIXME: home dir replacement should only
        # occur when current location is the file system
        # (SessionState.Path contains both CurrentLocation and
        # CurrentFileSystemLocation)
        $s = $ExecutionContext.SessionState.Path.CurrentLocation
        if ($script:Options.ReplaceHome) {
            # replace home path with ":~"; since "~" alone is a valid
            # directory name, an extra, invalid path char (colon) is used
            $s = $s -replace ([RegEx]::Escape($HOME)+'(?:$|(?=\\))'),':~'
        }
        if ($script:Options.PathDisplay -eq 'Tail') {
            $s = Split-Path -Leaf $s
        }
    }
    $s
}


Add-ModPromptItem -Id 'Nesting' -Color 'w+/n+' -Expression {
    '>' * ($NestedPromptLevel + 1)
}


Export-ModuleMember *-*
