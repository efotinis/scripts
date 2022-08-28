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
    Register 'video'    '3gp avi divx flv m4v mkv mov mp4 mpeg mpg rm rmvb webm wmv'
    Register 'audio'    'aac ape flac m4a mid mp3 ogg ra ram wav'
    Register 'image'    'ani bmp cur gif ico jpeg jpg pcx png tga tif tiff webp xcf'
    Register 'archive'  '7z gz rar tar zip'
    Register 'binary'   'bin chm com dat djv djvu dll docx epub exe fnt fon lib lnk mobi obj ocx par2 pdf pif pyc pyd scr torrent ttf vxd xps'
   #Register 'binary:document'
   #Register 'binary:code'
   #Register 'binary:generic'
    Register 'text'     'awk bas bat c cfg cmd conf cpp css csv cue diff diz gitignore h hgignore hpp htm html inf ini js json log lua m3u m3u8 markdown md nfo php pls ps1 ps1xml psm1 py pyw sfv srt sub theme txt url vbs vtt xml xsl yml'
    Register 'generic'  '!qb bak res'
   #Register 'text:code'    py, cpp, ps1
   #Register 'text:data'    ini, cfg, cue, xml
   #Register 'text:generic' txt, md
    $knownExtType[''] = 'generic'

    # others: jar,rtf,doc,mdf,par,aspx,swf,wri

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
