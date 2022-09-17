Set-StrictMode -Version Latest


$script:Options = @{

    # Default for items that don't specify a color.
    DefaultColor = 'w+/n+'

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
    $fgDef, $bgDef = global:Get-ColorAttribute $script:Options.DefaultColor
    if ($null -eq $fgDef) {
        $fgDef = [System.Console]::ForegroundColor
    }
    if ($null -eq $bgDef) {
        $bgDef = [System.Console]::BackgroundColor
    }
    foreach ($c in $script:Components) {
        if ($null -ne $c.Expression) {
            $fg, $bg = global:Get-ColorAttribute $c.Color
            $args = @{
                Object = & $c.Expression
                NoNewLine = $true
                ForegroundColor = if ($null -ne $fg) { $fg } else { $fgDef }
                BackgroundColor = if ($null -ne $bg) { $bg } else { $bgDef }
            }
            Write-Host @args
        }
    }
    # HACK: A non-empty value must be ouput, otherwise Write-Host is buffered,
    # no output is produced and the default, fallback prompt ("PS>") is used
    # instead.
    Write-Output ' '
}


function Set-ModPromptOption {
    [CmdletBinding()]
    param(
        [string]$DefaultColor,

        [ValidateSet('Full', 'Tail', 'None')]
        [string]$PathDisplay,

        [bool]$ReplaceHome
    )
    if ($PSBoundParameters.ContainsKey('DefaultColor')) {
        $script:Options.DefaultColor = $DefaultColor
    }
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


# Calculate position from Index, Before or After.
# Only the parameter specified by How is used.
# If Index is out of bounds or Before/After do not exist, the number of
# components is returned, i.e. the end of the array.
function CalculatePosition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('Index', 'Before', 'After')]
        [string]$How,

        [int]$Index,

        [string]$Before,

        [string]$After
    )
    $count = $script:Components.Count
    switch ($How) {
        'Index' {
            if ($Index -lt 0 -or $Index -gt $count) {
                $Index = $count
            }
        }
        'Before' {
            $Index = script:GetComponentIndex $Before
            if ($Index -eq -1) {
                $Index = $count
            }
        }
        'After' {
            $Index = script:GetComponentIndex $After
            if ($Index -eq -1) {
                $Index = $count
            } else {
                ++$Index
            }
        }
    }
    return $Index
}


function Add-ModPromptItem {
    [CmdletBinding(DefaultParameterSetName = 'Index')]
    param(
        [Parameter(Mandatory)]
        [string]$Id,

        [string]$Color,

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
    $Index = CalculatePosition $PSCmdlet.ParameterSetName $Index $Before $After
    $script:Components.Insert($Index, [PSCustomObject]@{
        Id = $Id
        Color = if ($PSBoundParameters.ContainsKey('Color')) {
            $Color
        } else {
            $null
        }
        Expression = if ($PSBoundParameters.ContainsKey('Expression')) {
            $Expression
        } else {
            $null
        }
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


Add-ModPromptItem -Id 'Path' -Expression {
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


Add-ModPromptItem -Id 'Nesting' -Expression {
    '>' * ($NestedPromptLevel + 1)
}


Export-ModuleMember *-*
