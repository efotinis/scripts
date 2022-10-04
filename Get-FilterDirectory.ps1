<#
.SYNOPSIS
    Recursively list directories, skipping items based on name pattern.

.DESCRIPTION
    Get all subdirectories of the source directories (including themselves),
    provided their names do not match any of the wildcard patterns.

    Can be used to exclude meta directories (e.g. .git, .vscode, __pycache__)
    when searching for actual user files (see examples).

.PARAMETER InputObject
    Source directories to list subdirectories from. They are also included
    in the output, with the same filtering applied to them. Wildcards allowed.
    Default is the current directory.

.PARAMETER Pattern
    One or more wildcard patterns to match directory names against.
    If a directory matches any of them, it is excluded from the output.

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
param(
    [Parameter(Position = 0, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('FullName', 'Path')]
    [SupportsWildcards()]
    [string[]]$InputObject = '.',

    [Parameter(Mandatory, Position = 1)]
    [string[]]$Pattern
)
begin {
    function ProcessDir {
        param(
            [Parameter(ValueFromPipeline)]$Dir,
            [Parameter(Position = 0)]$Patt
        )
        process {
            $Dir | Get-IfProperty Name -NotLikeAny $Patt | % {
                Write-Output $_
                gci -dir $_.FullName | ProcessDir -Patt $Patt
            }
        }
    }
}
process {
    foreach ($dir in $InputObject) {
        gi $dir | ProcessDir -Patt $Pattern
    }
}
