Set-StrictMode -Version Latest


$script:Options = @{

    # Default for items that don't specify a color.
    DefaultColor = 'w+/n+'

    # Part of current path to display:
    #   - 'Full': Whole path.
    #   - 'Tail': Last component.
    #   - 'DriveTail': Drive and last component.
    #   - 'None': Nothing.
    PathDisplay = 'DriveTail'

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

        [ValidateSet('Full', 'Tail', 'DriveTail', 'None')]
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

        [string]$Description,

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
        Description = if ($PSBoundParameters.ContainsKey('Description')) {
            $Description
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


function Set-ModPromptItem {
    [CmdletBinding(DefaultParameterSetName = 'Index')]
    param(
        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [string]$Id,

        [string]$Color,

        [scriptblock]$Expression,

        [string]$Description,

        [Parameter(ParameterSetName = 'Index')]
        [int]$Index,

        [Parameter(ParameterSetName = 'Before')]
        [string]$Before,

        [Parameter(ParameterSetName = 'After')]
        [string]$After
    )
    $oldPos = script:GetComponentIndex $Id
    if ($oldPos -eq -1) {
        Write-Error "Item Id does not exists: $Id"
        return
    }
    $psn = $PSCmdlet.ParameterSetName
    if ($psn -eq 'Index' -and -not $PSBoundParameters.ContainsKey('Index')) {
        $newPos = $oldPos
    } else {
        $newPos = CalculatePosition $psn $Index $Before $After
    }
    if ($newPos -ne $oldPos) {
        $item = $script:Components[$oldPos]
        $script:Components.RemoveAt($oldPos)
        if ($newPos -gt $oldPos) {
            --$newPos
        }
        $script:Components.Insert($newPos, $item)
    }
    if ($PSBoundParameters.ContainsKey('Color')) {
        $script:Components[$newPos].Color = $Color
    }
    if ($PSBoundParameters.ContainsKey('Expression')) {
        $script:Components[$newPos].Expression = $Expression
    }
    if ($PSBoundParameters.ContainsKey('Description')) {
        $script:Components[$newPos].Description = $Description
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


Add-ModPromptItem -Id 'Admin' -Color 'w+/r' -Expression {
    if (IsAdmin) {
        'ADMIN:'
    } else {
        ''
    }
} -Description 'Elevated session indicator.'


Add-ModPromptItem -Id 'Jobs' -Color 'w+/b' -Expression {
    $a = @(Get-Job)
    if ($a.Count -gt 0) {
        "{0}j:" -f $a.Count
    } else {
        ''
    }
} -Description 'Number of background jobs, if any.'


Add-ModPromptItem -Id 'Path' -Expression {
    $loc = $ExecutionContext.SessionState.Path.CurrentLocation
    $path = $loc.Path
    $drive = Split-Path -Qualifier $path
    $tail = Split-Path -Leaf $path
    $path = switch ($script:Options.PathDisplay) {
        None { '' }
        Full { $path }
        Tail { $tail }
        DriveTail { $drive + $tail }
    }
    $isFileSys = $loc.Provider.Name -eq 'FileSystem'
    if ($isFileSys -and $script:Options.ReplaceHome) {
        # Match to the end of path or followed by a path separator.
        $homeRx = '^' + [RegEx]::Escape($HOME) + '(?:$|(?=\\))'
        # Replace with special token, to disambiguate from literal '~'.
        $path -replace $homeRx,':~'
    } else {
        $path
    }
} -Description 'Current path. Configurable via PathDisplay and ReplaceHome.'


Add-ModPromptItem -Id 'Level' -Expression {
    '>' * ($NestedPromptLevel + 1)
} -Description 'Prompt nesting level. Top level is ">".'


Export-ModuleMember *-*
