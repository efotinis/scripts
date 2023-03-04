[CmdletBinding(DefaultParameterSetName = 'Path')]
param(
    <#
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias( <-#'PSPath',#-> 'FullName')]
    [string[]]$InputObject
    #>
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName, Position=0, ParameterSetName = 'Path')]
    [SupportsWildcards()]
    [string[]]$Path,

    [Parameter(Mandatory, ValueFromPipelineByPropertyName, ParameterSetName = 'LiteralPath')]
    [Alias('PSPath')]
    [string[]]$LiteralPath
)

begin {

    Set-StrictMode -Version Latest

    Add-Type -TypeDefinition @"
        using int64 = System.Int64;
        public struct VideoInfo
        {
            public string   Container;
            public int[]    StreamCounts;
            public int      Width;
            public int      Height;
            public double   Duration;
            public int      Bitrate;
            public double   Framerate;
            public string   FramerateRatio;
            public string   Video;
            public string   VideoTag;
            public string   Audio;
            public string   AudioTag;
            public int      Channels;
            public int64    Length;
            public string   FullName;
            public VideoInfo(
                string container, int[] streamCounts, int width, int height, double duration, int bitrate, double framerate, string framerateRatio,
                string video, string videoTag, string audio, string audioTag, int channels, int64 length,
                string fullName)
            {
                Container = container;
                StreamCounts = streamCounts;
                Width = width;
                Height = height;
                Duration = duration;
                Bitrate = bitrate;
                Framerate = framerate;
                FramerateRatio = framerateRatio;
                Video = video;
                VideoTag = videoTag;
                Audio = audio;
                AudioTag = audioTag;
                Channels = channels;
                Length = length;
                FullName = fullName;
            }
            public string PSPath {
                get { return FullName; }
            }
        }
"@

    # Check for thumbnail. Not sure if totally accurate.
    function IsMjpegWithoutRate ($Stream) {
        $Stream.codec_name -eq 'mjpeg' -and $Stream.avg_frame_rate -eq '0/0'
    }

    filter IsVideoStream {
        if ($_.codec_type -eq 'video' -and -not (IsMjpegWithoutRate $_)) {
            $_
        }
    }

    filter IsAudioStream {
        if ($_.codec_type -eq 'audio') {
            $_
        }
    }

    # Get 4-tuple of stream type counts:
    #   [0]: video
    #   [1]: audio
    #   [2]: subtitles
    #   [3]: other; includes thumbnails, mov_text, and embedded fonts
    function GetStreamTypesCount ($Streams) {
        $ret = @(0,0,0,0)
        foreach ($s in $Streams) {
            $i = switch ($s.codec_type) {
                video {
                    if (IsMjpegWithoutRate $s) { 3 } else { 0 }
                }
                audio { 1 }
                subtitle { 2 }
                default { 3 }
            }
            $ret[$i] += 1
        }
        $ret
    }

    function fps_value ($Ratio) {
        if ($Ratio -eq '0/0') {
            0
        } else {
            $a, $b = $Ratio -split '/',2
            $a / $b
        }
    }

    function CodecTag ([string]$s) {
        $s -replace '\[0\]',"`0"
    }

    $inputItems = [System.Collections.ArrayList]@()

}

process {

    $a = @(switch ($PSCmdlet.ParameterSetName) {
        'Path' {
            Get-Item -Path $Path | ? PSIsContainer -eq $false
        }
        'LiteralPath' {
            Get-Item -LiteralPath $LiteralPath | % {
                if (-not $_.PSIsContainer) {
                    $_
                } else {
                    Write-Error "Path is a directory: $LiteralPath"
                }
            }
        }
    })
    [void]$inputItems.AddRange($a)

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
        $acodec = if ($audio) { $audio.codec_name } else { $null }
        $channels = if ($audio) { $audio.channels } else { $null }
        $vctag = CodecTag $video.codec_tag_string
        $actag = if ($audio) { CodecTag $audio.codec_tag_string } else { '' }

        [VideoInfo]::new(
            $format.format_long_name,
            (GetStreamTypesCount $info.streams),
            [int]$video.width,
            [int]$video.height,
            [double]$format.duration,
            [int]$format.bit_rate,
            (fps_value $video.avg_frame_rate),
            $video.avg_frame_rate,
            $vcodec,
            $vctag,
            $acodec,
            $actag,
            $channels,
            [int64]$format.size,
            $item
        )
    }

    Write-Progress @progress -Completed

}
