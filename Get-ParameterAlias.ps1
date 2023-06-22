<#
.SYNOPSIS
    Show parameter aliases.

.DESCRIPTION
    Gets parameter aliases of the specified commands in an easy to understand format.

    Also useful for PowerShell versions where a bug prevents aliases from been shown in Get-Help output.

.PARAMETER Command
    One or more command names or aliases. Wildcards allowed.

.PARAMETER All
    Include common parameters and parameters without aliases.

.INPUTS
    None

.OUTPUTS
    PSCustomObject

.EXAMPLE
    PS> Get-ParameterAlias ls

    Command             Parameter   Aliases
    -------             ---------   -------
    ls -> Get-ChildItem LiteralPath {PSPath}
    ls -> Get-ChildItem Recurse     {s}
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string[]] $Command,

    [switch] $All
)

$COMMON = [System.Collections.Generic.Hashset[string]]@(
    'Confirm'
    'Debug'
    'ErrorAction'
    'ErrorVariable'
    'InformationAction'
    'InformationVariable'
    'OutBuffer'
    'OutVariable'
    'PipelineVariable'
    'UseTransaction'
    'Verbose'
    'WarningAction'
    'WarningVariable'
    'WhatIf'
)


function GetCommandsFromParameter ([string[]]$Command) {
    foreach ($name in $Command) {
        $cmds = Get-Command -Name $name
        if ($? -and -not $cmds) {
            Write-Warning "not commands matched: $name"
            continue
        }
        $cmds
    }
}


function GetName ([System.Management.Automation.CommandInfo]$Command) {
    if ($Command.CommandType -eq 'Alias') {
        $Command.DisplayName
    } else {
        $Command.Name
    }
}


foreach ($cmd in (GetCommandsFromParameter $Command)) {
    $cmd.parameters.Values | % {
        if ($All -or ($_.aliases -and $_.name -notin $COMMON)) {
            [PSCustomObject]@{
                Command = GetName $cmd
                Parameter = $_.Name
                Aliases = $_.Aliases
            }
        }
    }
}
