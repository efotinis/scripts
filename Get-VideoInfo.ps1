[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias( <#'PSPath',#> 'FullName')]
    [string[]]$InputObject
)

begin {

    Set-StrictMode -Version Latest

    Add-Type -TypeDefinition @"
        using int64 = System.Int64;
        public struct VideoInfo
        {
            public int      Width;
            public int      Height;
            public double   Duration;
            public int      Bitrate;
            public double   Framerate;
            public string   Video;
            public string   VideoTag;
            public string   Audio;
            public int      Channels;
            public int64    Size;
            public string   Path;
            public VideoInfo(
                int width, int height, double duration, int bitrate, double framerate, 
                string video, string videoTag, string audio, int channels, int64 size, 
                string path) 
            {
                Width = width;
                Height = height;
                Duration = duration;
                Bitrate = bitrate;
                Framerate = framerate;
                Video = video;
                VideoTag = videoTag;
                Audio = audio;
                Channels = channels;
                Size = size;
                Path = path;
            }
        }
"@

    filter IsVideoStream {
        if ($_.codec_type -eq 'video' -and $_.avg_frame_rate -ne '0/0') {
            $_
        }
    }

    filter IsAudioStream {
        if ($_.codec_type -eq 'audio') {
            $_
        }
    }

    function fps_value ($Ratio) {
        $a, $b = $Ratio -split '/',2
        $a / $b
    }

    function CodecTag ([string]$s) {
        $s -replace '\[0\]',"`0"
    }
    
    # Testing if a path is a valid file.
    #
    # Notes:
    # - "Test-Path -Type Leaf -LiteralPath $Path" returns false (in PS5.1)
    #   if the parent path contains brackets.
    # - "Resolve-Path -LiteralPath $Path" returns missing parent path parts
    #   containing brackets errorneously preceeded by backticks (in PS5.1).
    #   Maybe that's the reason Test-Path fails.
    # - One way to test is to use [IO.File]::GetAttributes, but that requires
    #   either a relative path (using the process CWD and not PowerShell's),
    #   or an absolute path. As mentioned above, we can't reliably get the
    #   absolute path using Resolve-Path and [IO.Path]::GetFullPath also uses
    #   the process CWD instead of PowerShell's. The only way is to use 
    #   GetUnresolvedProviderPathFromPSPath.
    # - The rest is easy. /s
    function TestPathIsFile ([string]$Path) {
        try {
            # from: https://gist.github.com/sayedihashimi/02e98613efcb7280d706
            $abs = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
            $attr = [IO.File]::GetAttributes($abs)
            ($attr -band [IO.FileAttributes]::Directory) -eq 0
        } catch {
            $false
        }
    }

    $inputItems = [System.Collections.ArrayList]@()

}

process {

    $inputItems += @($InputObject)

}

end {

    $progress = @{
        Activity='Extracting video information'
    }
    $progressIndex = 0

    foreach ($item in $inputItems) {
        $progressIndex += 1
        $progress.CurrentOperation = $item
        $progress.Status = "$progressIndex of $($inputItems.Count)"
        $progress.PercentComplete = ($progressIndex - 1) / $inputItems.Count * 100
        Write-Progress @progress
        
        if (-not (TestPathIsFile $item)) {
            Write-Error -Message 'path is not a file' -TargetObject $item
            continue
        }
        
        $info = avprobe.exe $item -show_format -show_streams -of json -v 0 | ConvertFrom-Json
        if (-not ($info | Get-Member format) -or -not ($info | Get-Member streams)) {
            Write-Error -Message 'could not get video info' -TargetObject $item
            continue
        }
        $format = $info.format
        $video = $info.streams | IsVideoStream | select -first 1
        $audio = $info.streams | IsAudioStream | select -first 1

        if (-not $video) {
            Write-Error -Message 'could not find video stream' -TargetObject $item
            continue
        }

        $vcodec = $video.codec_name
        $acodec = & { if ($audio) { $audio.codec_name } else { $null } }
        $channels = & { if ($audio) { $audio.channels } else { $null } }

        [VideoInfo]::new(
            [int]$video.width, 
            [int]$video.height, 
            [double]$format.duration, 
            [int]$format.bit_rate, 
            (fps_value $video.avg_frame_rate), 
            $vcodec,
            (CodecTag $video.codec_tag_string),
            $acodec,
            $channels,
            [int64]$format.size, 
            $item
        )
    }

    Write-Progress @progress -Completed

}
