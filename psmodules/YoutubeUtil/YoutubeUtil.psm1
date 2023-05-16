#requires -Modules NiceConvert

# YouTube-related functions.


function global:yc {  # play youtube stream from clipboard url
    param(
        [switch]$HiDef,  # use high quality stream, if available
        [int]$TailView = 0  # if >0, prompt to launch in browser at specified seconds before end; useful to mark video as watched
    )
    Function GetYouTubeIdFromUrl ([string]$Url) {
        if ($Url -match 'https://www\.youtube\.com/watch\?v=(.{11})') {
            return $Matches[1]
        }
        if ($Url -match '(.{11})') {
            return $Matches[1]
        }
        Write-Error "could not find ID in URL: $Url"
    }
    $id = GetYouTubeIdFromUrl (Get-Clipboard)
    $fmt = if ($HiDef) { 22,18 } else { 18 }
    yps -f $fmt -- $id
    if ($TailView -gt 0) {
        Write-Host -NoNewLine "getting video info...`r"
        $info = yd -j -- $id | ConvertFrom-Json
        $timestamp = $info.duration - $TailView
        Read-Host 'press Enter to launch in browser' > $null
        Start-Process "https://youtube.com/watch?v=${id}&t=${timestamp}"
    }
}


# get youtube-dl local/remote versions
function global:ydv {
    function LatestVersion {
        $r = Invoke-WebRequest -Uri 'https://yt-dl.org/update/LATEST_VERSION'
        ($r.Content -as [char[]]) -join ''
    }
    function VersionToAge ([string]$Version) {
        ConvertTo-NiceAge ((Get-Date).Date - (Get-Date $Version))
    }
    $local = youtube-dl.exe --version
    [PSCustomObject]@{
        Program='youtube-dl'
        Type='Local'
        Version=$local
        Age=VersionToAge $local
    }
    $latest = LatestVersion
    [PSCustomObject]@{
        Program='youtube-dl'
        Type='Latest'
        Version=$latest
        Age=VersionToAge $latest
    }
}


# Get YouTube video info.
function global:yvjson {
    param(
        [string]$Url,
        [switch]$Full  # do not strip verbose fields
    )
    $a = yd -ij -- $Url | ConvertFrom-Json
    if (-not $Full) {
        $a = $a | select * -exclude formats,requested_formats,thumbnails,urls,automatic_captions
    }
    return $a
}


# Get most relevant YouTube video info.
function global:yvinfo {
    param(
        [string]$Url
    )
    yvjson -Url $Url | select @(
        'id'
        'title'
        'uploader'
        'upload_date'
        'duration_string'
        'channel_follower_count'
        'view_count'
        'age_limit'
        'categories'
        'tags'
        'description'
    )
}


# Get YouTube video auto-generated subtitles.
function global:yvsubs {
    <#param(
        [string]$Url,
        [string]$Language = 'en'
    )

    $tempPath = [System.IO.Path]::GetTempFileName()
    if ($tempPath) {
        # delete automatically created 0-length file; only path is needed
        Remove-Item -LiteralPath $tempPath
    } else {
        return
    }
    
    $args = @(
        '-o', $tempPath
        '--skip-download'
        '--write-auto-subs'
        '--sub-lang', $Language
        '--sub-format', 'ttml'
        '--'
        $Url
    )
    yt-dlp.exe @args > $null
    if ($?) {
        $filePath = "$tempPath.$Language.ttml"
        $x = [xml](Get-Content -LiteralPath $filePath -Encoding Utf8)
        Remove-Item -LiteralPath $filePath
        $x.tt.body.div.p
    }#>
    param(
        [string]$Url,
        [string]$Language = 'en',
        [switch]$Raw,     # output unprocessed data (overrides -Simple)
        [switch]$Simple,  # join multi-line entries
        [switch]$List
    )

    function ListSubs ($Items, [string]$Type) {
        $Items.PSObject.Properties.ForEach{
            [PSCustomObject]@{
                Type=$Type
                Language=$_.name
                Name=$_.value[0].name
            }
        }
    }

    function GetSub ($Info, [string]$Language, [string]$Format) {
        $a = @(
            $info.subtitles.$Language
            $info.automatic_captions.$Language
        ) | ? ext -eq $Format | select -first 1
        if (-not $a) {
            Write-Error "no subtitles match language ""$Language"" and format ""$Format"""
            return
        }
        $xml = Invoke-RestMethod -Uri $a.url
        $xml.tt.body.div.p
    }

    filter SingleLineOutput {
        [PSCustomObject]@{
            Time = $_.begin
            Text = @($_.'#text') -join ' '
        }
    }

    filter MultipleLineOutput {
        $time = $_.begin
        $first = $true
        $_.'#text' | % {
            [PSCustomObject]@{
                Time = if ($first) { $time } else { $null }
                Text = $_
            }
            $first = $false
        }
    }

    $info = yd -j -- $Url | ConvertFrom-Json

    if ($List) {
        
        ListSubs $info.subtitles 'subtitle'
        ListSubs $info.automatic_captions 'automatic_caption'

    } else {

        $a = GetSub $info $Language 'ttml'
        if ($Raw) {
            $a
        } elseif ($Simple) {
            $a | SingleLineOutput
        } else {
            $a | MultipleLineOutput
        }

    }
}


