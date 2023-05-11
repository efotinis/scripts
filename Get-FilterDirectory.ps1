#requires -Modules PipelineUtil

<#
.SYNOPSIS
    Recursively list directories, skipping items based on name pattern.

.DESCRIPTION
    Get all subdirectories of the source directories (including themselves),
    provided their names do not match any of the wildcard patterns.

    Can be used to exclude meta directories (e.g. .git, .vscode, __pycache__)
    when searching for actual user files (see examples).

.PARAMETER Path
    Source directories to list subdirectories from. They are also included
    in the output, with the same filtering applied to them. Wildcards allowed.
    Default is the current directory.

.PARAMETER LiteralPath
    Same as Path, but without wildcard expansion.

.PARAMETER Pattern
    One or more wildcard patterns to match directory names against.
    If a directory matches any of them, it is excluded from the output.

.PARAMETER Force
    Include hidden and system directories.

.INPUTS
    Source directories.

.OUTPUTS
    Directories matching criteria.

.EXAMPLE
    PS C:\> Get-FilterDirectory.ps1 C:\Projects\* -Pattern .*

    Get all dirs and subdirs under C:\Projects as long as they don't have
    a dot as the initial character.

.EXAMPLE
    PS C:\> Get-Item C:\script* |
    >> Get-FilterDirectory.ps1 -Pattern .*,__pycache__ |
    >> Get-ChildItem -File |
    >> Select-String ClassFactoryManagerProxy

    This command searches a string in all files of all directories named
    'script*' in C:\, excluding directories starting with a dot or named
    __pycache__.

    The pipeline steps are the following:
        - Get-Item selects the top-level directories.
        - Get-FilterDirectory gets all subdirs excluding unwanted ones.
        - Get-ChildItem selects all files.
            NOTE: Get-ChildItem must specify only File and neither Dir or
            Recurse for the whole command to work as intended.
        - Select-String searches the file contents.
#>
[CmdletBinding(DefaultParameterSetName = 'Path')]
param(
    [Parameter(ValueFromPipeline, ValueFromPipelineByPropertyName, ParameterSetName = 'Path')]
    [SupportsWildcards()]
    [string[]]$Path = '.',

    [Parameter(ValueFromPipelineByPropertyName, ParameterSetName = 'LiteralPath')]
    [Alias('PSPath')]
    [string[]]$LiteralPath,

    [Parameter(Mandatory, Position = 0)]
    [string[]]$Pattern,

    [switch]$Force
)
begin {
    Set-StrictMode -Version Latest
    function ProcessItem {
        param(
            [Parameter(ValueFromPipeline)]$Directory,
            [Parameter(Position = 0)]$Pattern
        )
        process {
            $Directory | Get-IfProperty Name -NotLikeAll $Pattern | % {
                Write-Output $_
                $_ | Get-ChildItem -Directory -Force:$Force | ProcessItem $Pattern
            }
        }
    }
    function ResolveInput {
        $opt = switch ($PSCmdlet.ParameterSetName) {
            'Path' { @{ Path = $Path } }
            'LiteralPath' { @{ LiteralPath = $LiteralPath } }
        }
        Get-Item @opt -Force:$Force | ? PSIsContainer
    }
}
process {
    ResolveInput | ProcessItem $Pattern
}
