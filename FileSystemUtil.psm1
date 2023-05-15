#requires -Modules PipelineUtil


<#
.SYNOPSIS
    Filter files based on extension type.

.DESCRIPTION
    Selects files based on well-known broad extention type categories.

.PARAMETER InputObject
    The file to check. Can either specify one item as an argument or multiple
    items via the pipeline.

.PARAMETER ItemType
    One or more types to select. Possible values are:
        - Video
        - Audio
        - Image: Includes animated images, like GIF and ANI.
        - Archive: Files containing other files. Does not include documents
            or code modules stored as ZIP, e.g. DOCX, JAR. These are listed
            as Binary instead.
        - Text
        - Binary
        - Generic: Indeterminate type files, such as BAK or no extension.

.PARAMETER Unknown
    Select files whose type in not known. Suppresses warning about unknown
    types. See also Exclude option.

.PARAMETER Exclude
    Reverse the selection, i.e. select items not matching the specified
    criteria. If Unknown is also set, selects all known types.

.INPUTS
    File objects.

.OUTPUTS
    File objects.
#>
function Get-ExtensionCategory {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        $InputObject,

        [Parameter(Mandatory, Position=1, ParameterSetName='Known')]
        [ValidateSet('Video', 'Audio', 'Image', 'Archive', 'Text', 'Binary', 'Generic')]
        [Alias('Type')]
        [string[]]$ItemType,

        [Parameter(ParameterSetName='Unknown')]
        [switch]$Unknown,

        [Alias('Not')]
        [switch]$Exclude
    )
    <#
        TODO:
        - in case of dubious type, issue warning (either per item or collectively)
    #>
    begin {
        Set-StrictMode -Version Latest

        $knownExtType = @{}
        function Register ([string]$Type, [string]$Extensions) {
            @($Extensions.Trim() -split '\s+').ForEach{
                $knownExtType['.' + $_] = $Type
            }
        }
        Register 'video'    '3gp asf avi divx flv m4v f4v mkv mov mp4 mpeg mpg rm rmvb webm wmv'
        Register 'audio'    'aac ape flac it m4a m4b m4r f4a f4b mid mod mp2 mp3 ogg opus ra ram s3m umx wav wma xm'
        Register 'image'    'ani bmp cur gif ico jpeg jpg pcx png tga tif tiff webp xcf'
        Register 'archive'  '7z gz jar rar tar zip'
        Register 'archive'  'cb7 cba cbr cbt cbz'  # image containers
        Register 'binary'   'bin chm com dat djv djvu dll doc docx epub exe fnt fon iso lib lnk mdf mobi nrg obj ocx par par2 pdf pif pyc pyd rtf scr swf torrent ttf vxd wad wri xps'
        Register 'text'     'awk bas bat c cfg cmd conf cpp css csv cue diff diz gitignore h hgignore hpp htm html inf ini js json log lua m3u m3u8 markdown md md5 mht nfo php pls ps1 ps1xml psm1 py pyw reg sfv srt sub theme txt url vbs vtt xml xsl yml'
        Register 'generic'  '!qb bak res'
        $knownExtType[''] = 'generic'
        
        Register 'binary'   'odf odg odp ods odt'   # NOTE: actually ZIP archives
        Register 'text'     'fodg fodp fods fodt'   # NOTE: XML versions of the above

        $unknownExts = [System.Collections.Generic.Hashset[string]]@()  # NOTE: lowercase keys
    }
    process {
        $ext = $InputObject.Extension
        $type = $knownExtType[$ext]
        if ($PSCmdlet.ParameterSetName -eq 'Known') {
            if (-not $type) {
                [void]$unknownExts.Add($ext.ToLower())
            } else {
                if ($Exclude) {
                    if ($type -notin $ItemType) { $InputObject }
                } else {
                    if ($type -in $ItemType) { $InputObject }
                }
            }
        } else {  # 'Unknown'
            if ([bool]$type -eq $Exclude) {
                $InputObject
            }
        }
    }
    end {
        if ($PSCmdlet.ParameterSetName -eq 'Known') {
            if ($unknownExts.Count) {
                $s = ($unknownExts | sort) -join ', '
                Write-Warning "unknown extensions: $s"
            }
        }
    }
}


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
function Get-FilterDirectory {
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
}


<#
.SYNOPSIS
    Create file hardlinks.

.DESCRIPTION
    Creates hardlinks of all input files to the specified directory.

.PARAMETER InputObject
    Source file path. Can pass multiple values via the pipeline.

.PARAMETER Destination
    Output directory. Will be created if it does not exist.

.PARAMETER Force
    Overwrite existing output files.

.INPUTS
    Existing file path(s).

.OUTPUTS
    New file objects.

#>
function New-HardLink {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName', 'Path')]
        [string]$InputObject,

        [Parameter(Mandatory)]
        [string]$Destination,

        [switch]$Force
    )
    begin {
        try {
            $destExists = Test-Path -LiteralPath $Destination -Type Container
        } catch {
            Write-Error "Destination path is invalid: $Destination"
            exit
        }
        if (-not $destExists) {
            if (-not (New-Item -Path $Destination -Type Directory)) {
                exit
            }
        }
        function EscapeBrackets ([string]$s) {
            $s -replace '([[\]])','`$1'
        }
    }
    process {
        $name = Split-Path -Leaf -Path $InputObject
        $newPath = Join-Path -Path $Destination -ChildPath $Name
        $srcPath = EscapeBrackets $InputObject
        New-Item -Type HardLink -Path $newPath -Value $srcPath -Force:$Force
    }
}


<#
.SYNOPSIS
    Create filesystem objects with numeric prefix from existing items.

.DESCRIPTION
    Generates new file and directory objects from existing items and inserts
    an increasing index as a name prefix.

.PARAMETER Path
    Input item path. Wildcards are supported. Can specify multiple items either
    as an array or via the pipeline.

.PARAMETER LiteralPath
    Input item path. Wildcards are ignored. Can specify multiple items either
    as an array or via the pipeline.

.PARAMETER Destination
    Output directory. Will be created if needed.

.PARAMETER Operation
    Method of new item creation. One of:

        - Copy:         Files and directories are copied.
        - Link:         Hardlinks are created for files and junctions for
                        directories.
        - SymbolicLink: Symbolic links of files and directories are created.
                        This operation requires elevation.

.PARAMETER StartIndex
    Initial prefix number of created items. Default is 1.

.PARAMETER Shuffle
    Randomize the order of new items.

.INPUTS
    Input item paths.

.OUTPUTS
    New filesystem objects.
#>
function New-IndexedItem {
    [CmdletBinding(SupportsShouldProcess, DefaultParameterSetName = 'Path')]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName, Position = 0, ParameterSetName = 'Path')]
        [SupportsWildcards()]
        [string[]]$Path,

        [Parameter(Mandatory, ValueFromPipelineByPropertyName, ParameterSetName = 'LiteralPath')]
        [SupportsWildcards()]
        [Alias('PSPath')]
        [string[]]$LiteralPath,

        [Parameter(Mandatory)]
        [string]$Destination,

        [Parameter(Mandatory)]
        [ValidateSet('Copy', 'Link', 'SymbolicLink')]
        [string]$Operation,

        [int]$StartIndex = 1,

        [switch]$Shuffle
    )

    begin {
        Set-StrictMode -Version Latest
        $items = [System.Collections.ArrayList]@()

        # Handle item and return new item object.
        function ProcessItem ($SrcPath, $NewPath, $IsDir) {
            if ($Operation -eq 'Copy') {
                if ($IsDir) {
                    Copy-Item -LiteralPath $SrcPath -Destination $NewPath -Recurse
                    if ($?) { Get-Item -LiteralPath $NewPath }
                } else {
                    Copy-Item -LiteralPath $SrcPath -Destination $NewPath -PassThru
                }
            } else {
                if ($Operation -eq 'SymbolicLink') {
                    $type = 'SymbolicLink'
                } elseif ($IsDir) {
                    $type = 'Junction'
                } else {
                    $type = 'HardLink'
                }
                # NOTE: New-Item's `-Value` is incorrectly treated as a wildcard,
                # so brackets must be backtick-escaped. See issue Feb 24, 2018:
                #   https://github.com/PowerShell/PowerShell/issues/6232
                $SrcPath = $SrcPath -replace '([[\]])','`$1'
                New-Item -Type $type -Path $NewPath -Value $SrcPath
            }
        }

    }
    process {
        $a = @(switch ($PSCmdlet.ParameterSetName) {
            'Path' { Get-Item -Path $Path }
            'LiteralPath' { Get-Item -LiteralPath $LiteralPath }
        })
        [void]$items.AddRange($a)
    }
    end {
        # NOTE: Test destination explicitly instead of using `New-Item -Force`,
        # to report error if it's file and to avoid failure if it's a root path.
        $dest = Get-Item -LiteralPath $Destination -ErrorAction Ignore
        if ($dest -and -not $dest.PSIsContainer) {
            Write-Error "Destination path is a file: $Destination"
            return
        }
        if (-not $dest) {
            $dest = New-Item -Type Directory -Path $Destination
            if (-not $dest) {
                return
            }
        }

        if ($Shuffle) {
            $items = $items | Get-Random -Count $items.Count
        }

        $indexFormat = 'D' + ([string]$items.Count).Length
        $index = $StartIndex

        foreach ($item in $items) {
            $newName = $index.ToString($indexFormat) + '. ' + $item.Name
            $newPath = Join-Path $dest $newName
            ProcessItem $item.FullName $newPath $item.PSIsContainer
            ++$index
        }
    }
}


<#
.SYNOPSIS
    Rename files using regular expressions.

.DESCRIPTION
    Renames files using one or more pairs of match-replace regexp patterns.
    The match strings define capture groups to be used as capture references in
    the replace strings. Extra data per input can be specified and used as
    additional named captures.

.PARAMETER Path
    Input file paths. Supports wildcards.

.PARAMETER LiteralPath
    Input file paths. No wildcards allowed.

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
    File/directory objects or paths.

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
function Rename-Pattern {
    [CmdletBinding(DefaultParameterSetName = 'Path')]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName, ParameterSetName = 'Path')]
        [SupportsWildcards()]
        [string[]]$Path,

        [Parameter(Mandatory, ValueFromPipelineByPropertyName, ParameterSetName = 'LiteralPath')]
        [Alias('PSPath')]
        [string[]]$LiteralPath,

        [Parameter(Mandatory, Position = 0)]
        [string[]]$Match,

        [Parameter(Mandatory, Position = 1)]
        [AllowEmptyString()]
        [string[]]$Replace,

        [hashtable]$Extra,

        [ValidateSet('Never', 'Always', 'FilesOnly', 'DirsOnly')]
        [string]$IncludeExtension = 'DirsOnly',

        [switch]$Commit
    )

    begin {
        Set-StrictMode -Version Latest
        $items = [System.Collections.ArrayList]@()
        if ($null -eq $Extra) {
            $Extra = @{}
        }
        if ($Match.Count -ne $Replace.Count) {
            throw "Match and Replace must have the same number of values."
        }
        #function AssertExtraCounts($ $InputSize) {
        #}
    }
    process {
        $a = @(switch ($PSCmdlet.ParameterSetName) {
            'Path' { Get-Item -Path $Path }
            'LiteralPath' { Get-Item -LiteralPath $LiteralPath }
        })
        [void]$items.AddRange($a)
    }
    end {
        # TODO: implement title-case using
        #   [cultureinfo]::CurrentCulture.TextInfo.ToTitleCase(string)
        #   NOTE: this may need to be applied in specific text ranges
        #       e.g.:  for 's1e01 this is a title' the 's1e01' part should be uppercase
        #       and the rest titlecase
        # TODO: perhaps use scriptblock param for more customization
        # TODO: implement stored params by using (json) file to specify match/replace/etc

        $count = $items.Count

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

        function AffectExtension ($Item, $Mode) {
            switch ($Mode) {
                'Never' { $False }
                'Always' { $True }
                'FilesOnly' { -not $Item.PSIsContainer }
                'DirsOnly' { $Item.PSIsContainer }
            }
        }

        for ($i = 0; $i -lt $count; ++$i) {
            $orgName = $items[$i].Name

            if (AffectExtension $items[$i] $IncludeExtension) {
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
                $ret = if ($items[$i].Name -cne $newName) {
                    $items[$i] | Rename-Item -NewName $newName -PassThru
                }
                if ($ret) {
                    $wasRenamed = $true
                } else {
                    $ret = $items[$i]
                    $wasRenamed = $false
                }
                if ($ret) {
                    $ret | Add-Member -NotePropertyName Renamed -NotePropertyValue $wasRenamed
                    Write-Output $ret
                }
            }
            else {
                [PSCustomObject]@{
                    New = $orgName -cne $newName
                    NewName = $newName
                    Name = $items[$i].Name
                    Directory = [System.IO.Path]::GetDirectoryName($items[$i].FullName)
                }
            }
        }
    }
}


Export-ModuleMember -Function *-*
