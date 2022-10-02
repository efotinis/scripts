<#
.SYNOPSIS
    Rename files using regular expressions.

.DESCRIPTION
    Renames files using one or more pairs of match-replace regexp patterns.
    The match strings define capture groups to be used as capture references in
    the replace strings. Extra data per input can be specified and used as
    additional named captures.

.PARAMETER InputObject
    Input file paths.

.PARAMETER Match
    Regex string to search for. Parts of the file name that do not match remain
    unchanged. By default, the extension is only included for file paths.
    See also IncludeExtension and Extra.

    Multiple values can be specified and will be used in parallel with those
    in -Replace.

.PARAMETER Replace
    String to replace with. Can contain regex match references, like $1,
    ${name}, etc. See also Extra.

    If multiple values are specified for -Match, the same number of values must
    be specified for this parameter.

.PARAMETER Extra
    Hashtable of extra named captures to provide for each replacement. Can
    be used to provide data not found in the original strings (e.g. increment
    counter).

    Each key is the capture name and its corresponding value a list of strings.
    The strings are provided for each input item in order. The size of each
    list must match the number of input items.

.PARAMETER IncludeExtension
    Specify when to include the extension in the matching process. Possible
    values are 'Never', 'Always', 'FilesOnly', and 'DirsOnly' (default).

.PARAMETER Commit
    Perform the actual renaming operation. If omitted, output the potential
    results in the form of change flag, result name, and input path.

.EXAMPLE

.INPUTS
    None.

.OUTPUTS
    - If Commit is set, return file system objects of all input items with an
        additional property Renamed showing whether the name was changed.
    - If Commit is not set, return PSCustomObjects with info about how each
        input item would be affected.

.NOTES
    Rename-Item fails when renaming a directory with a different letter case.
    This is by design [1], since the PowerShell cmdlet uses .Net and
    IO.Directory::Move has the same limitation. This is not the case with
    IO.File::Move. Very inconsistent design, IMO.

        Workaround: add/remove characters and then remove/add them again.

    Rename-Item also fails for source files with brackets in their parent path,
    even when specifying relative paths that don't show those brackets.

        Workaround: (temporarily) remove brackets from parent directory names.

    [1]: https://github.com/PowerShell/PowerShell/issues/12483
         "Can't rename directory with the same name but different case"

    See also:
    - https://stackoverflow.com/questions/57347650
      "rename multiple folder to Uppercase not files using powershell"
        - https://github.com/dotnet/runtime/issues/30479
          "DirectoryInfo.MoveTo and Directory.Move mistakenly prevent renaming directories to case variations of themselves on Windows, macOS"
            - https://github.com/dotnet/corefx/pull/40570
              "Directory move fix"

#>

[CmdletBinding()]
param(
    [string[]]$InputObject,

    [string[]]$Match,

    [string[]]$Replace,

    [hashtable]$Extra,

    [ValidateSet('Never', 'Always', 'FilesOnly', 'DirsOnly')]
    [string]$IncludeExtension = 'DirsOnly',

    [switch]$Commit
)


# TODO: implement title-case using
#   [cultureinfo]::CurrentCulture.TextInfo.ToTitleCase(string)
#   NOTE: this may need to be applied in specific text ranges
#       e.g.:  for 's1e01 this is a title' the 's1e01' part should be uppercase
#       and the rest titlecase
# TODO: perhaps use scriptblock param for more customization
# TODO: implement input pipeline


$count = $InputObject.Count

# Make sure Match and Replace are the same size.
if ($Match.Count -ne $Replace.Count) {
    Write-Error "Match and Replace must have the same number of values."
    return
}

# Make sure extra field data counts match input file count.
if ($Extra.Count) {
    $mismatchedFields = @()
    foreach ($item in $Extra.GetEnumerator()) {
        if ($item.Value.Count -ne $count) {
            $mismatchedFields += "$($item.Key) (=$($item.Value.Count))"
        }
    }
    if ($mismatchedFields.Count) {
        $msg = "file count ($count)) does not match extra field count: " +
            ($mismatchedFields -join ', ')
        Write-Error $msg
        return
    }
}

function AffectExtension ($Path, $Mode) {
    switch ($Mode) {
        'Never' { $False }
        'Always' { $True}
        'FilesOnly' { Test-Path -LiteralPath $Path -Type Leaf }
        'DirsOnly' { Test-Path -LiteralPath $Path -Type Container }
    }
}

for ($i = 0; $i -lt $count; ++$i) {
    $orgName = [IO.Path]::GetFileName($InputObject[$i])

    if (AffectExtension $InputObject[$i] $IncludeExtension) {
        $stem = $orgName
        $ext = ''
    } else {
        $stem = [IO.Path]::GetFileNameWithoutExtension($orgName)
        $ext = [IO.Path]::GetExtension($orgName)
    }

    $s = $stem
    for ($step = 0; $step -lt $Match.Count; ++$step) {
        $s = $s -replace $Match[$step],$Replace[$step]
    }
    if ($Extra.Count) {
        foreach ($item in $Extra.GetEnumerator()) {
            $s = $s -replace ('\${'+$item.Key+'}'),$item.Value[$i]
        }
    }
    $newName = $s + $ext

    if ($Commit) {
        if ($InputObject[$i] -cne $newName) {
            $ret = Rename-Item -LiteralPath $InputObject[$i] -NewName $newName -PassThru
        }
        if ($ret) {
            $wasRenamed = $true
        } else {
            $ret = Get-Item -LiteralPath $InputObject[$i]
            $wasRenamed = $false
        }
        if ($ret) {
            $ret | Add-Member -NotePropertyName Renamed -NotePropertyValue $wasRenamed
            Write-Output $ret
        }
    }
    else {
        [PSCustomObject]@{
            Change=$orgName -cne $newName
            Name=$newName
            Input=$InputObject[$i]
        }
    }
}
