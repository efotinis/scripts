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


$script:Components = [System.Collections.ArrayList]::new()


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



# Get index of component with matching Id, or -1 if not found.
function GetComponentIndex ([string]$Id) {
    for ($i = 0; $i -lt $script:Components.Count; ++$i) {
        if ($script:Components[$i].Id -eq $Id) {
            return $i
        }
    }
    return -1
}


function Add-ModPromptItem {
    [CmdletBinding(DefaultParameterSetName = 'Index')]
    param(
        [Parameter(Mandatory)]
        [string]$Id,

        [Parameter(Mandatory)]
        [string]$Color,

        [Parameter(Mandatory)]
        [scriptblock]$Expression,

        [Parameter(ParameterSetName = 'Index')]
        [int]$Index = -1,

        [Parameter(ParameterSetName = 'Before')]
        [string]$Before,

        [Parameter(ParameterSetName = 'After')]
        [string]$After
    )
    if ((script:GetComponentIndex $Id) -ge 0) {
        Write-Error "Item Id already exists: $Id"
        return
    }
    $compCount = $script:Components.Count
    switch ($PSCmdlet.ParameterSetName) {
        Index {
            if ($Index -lt 0 -or $Index -gt $compCount) {
                $Index = $compCount
            }
        }
        Before {
            $Index = script:GetComponentIndex $Before
            if ($Index -lt 0) {
                $Index = $compCount
            }
        }
        After {
            $Index = script:GetComponentIndex $After
            if ($Index -lt 0) {
                $Index = $compCount
            } else {
                ++$Index
            }
        }
    }
    $script:Components.Insert($Index, [PSCustomObject]@{
        Id = $Id
        Color = $Color
        Expression = $Expression
    })
}


function Get-ModPromptItem {
    [CmdletBinding(DefaultParameterSetName = 'Id')]
    param(
        [Parameter(ParameterSetName = 'Id', Position = 0)]
        [string]$Id = '*',

        [Parameter(ParameterSetName = 'Index', Position = 0)]
        [int[]]$Index
    )
    switch ($PSCmdlet.ParameterSetName) {
        Id {
            $script:Components | ? Id -Like $Id
        }
        Index {
            $script:Components | select -Index $Index
        }
    }
}


function Remove-ModPromptItem {
    [CmdletBinding(DefaultParameterSetName = 'Id')]
    param(
        [Parameter(ParameterSetName = 'Id', Position = 0)]
        [string]$Id = '*',

        [Parameter(ParameterSetName = 'Index', Position = 0)]
        [int[]]$Index
    )
    $ids = script:Get-ModPromptItem @PSBoundParameters | % Id
    $ids | % {
        $i = GetComponentIndex $_
        if ($i -ge 0) {
            $script:Components.RemoveAt($i)
        }
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
