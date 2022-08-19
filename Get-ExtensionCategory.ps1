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
    Register 'video'    'mp4 avi mpg mpeg mkv divx mov 3gp webm wmv flv m4v rm rmvb'
    Register 'audio'    'mp3 m4a wav ogg flac aac mid ape ra ram'
    Register 'image'    'bmp pcx gif png jpg jpeg tif tiff tga xcf ico cur ani webp'
    Register 'archive'  'zip rar 7z tar gz'
    Register 'binary'  ('par2 pdf docx bin dat pyc lnk xps exe obj torrent chm epub ' + 
                        'lib com djv djvu mobi pif scr dll fnt ttf fon ocx vxd pyd')
   #Register 'binary:document'
   #Register 'binary:code'
   #Register 'binary:generic'
    Register 'text'    ('txt ini cfg conf htm html css js vbs json srt inf nfo ps1 psm1 ps1xml cue ' + 
                        'c h cpp hpp py pyw log url csv md markdown xml bas bat cmd awk m3u m3u8 pls theme ' + 
                        'xsl lua php diz yml gitignore hgignore diff vtt')
    Register 'generic'  'bak res'
   #Register 'text:code'    py, cpp, ps1
   #Register 'text:data'    ini, cfg, cue, xml
   #Register 'text:generic' txt, md
   
    $knownExtType[''] = 'generic'
   
   # jar,rtf,doc,mdf,par,aspx,swf,wri
   
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
