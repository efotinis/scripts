[CmdletBinding(DefaultParameterSetName = 'Path')]
param(
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
            public string   Format;
            public string   FormatRaw;
            public string   FormatDescr;
            public int[]    StreamCounts;
            public int      Width;
            public int      Height;
            public double   Duration;
            public int      Bitrate;
            public int      VideoBitrate;
            public int      AudioBitrate;
            public double   Framerate;
            public string   FramerateRatio;
            public string   Video;
            public string   VTag;
            public string   VTagRaw;
            public string   Audio;
            public string   ATag;
            public string   ATagRaw;
            public int      Channels;
            public int64    Length;
            public string   FullName;
            public VideoInfo(
                string format, string formatRaw, string formatDescr, int[] streamCounts, int width, int height, double duration, int bitrate, int videoBitrate, int audioBitrate, double framerate, string framerateRatio,
                string video, string vtag, string vtagRaw, string audio, string atag, string atagRaw, int channels, int64 length,
                string fullName)
            {
                Format = format;
                FormatRaw = formatRaw;
                FormatDescr = formatDescr;
                StreamCounts = streamCounts;
                Width = width;
                Height = height;
                Duration = duration;
                Bitrate = bitrate;
                VideoBitrate = videoBitrate;
                AudioBitrate = audioBitrate;
                Framerate = framerate;
                FramerateRatio = framerateRatio;
                Video = video;
                VTag = vtag;
                VTagRaw = vtagRaw;
                Audio = audio;
                ATag = atag;
                ATagRaw = atagRaw;
                Channels = channels;
                Length = length;
                FullName = fullName;
            }
            public string PSPath {
                get { return FullName; }
            }
            public string Name {
                get { return System.IO.Path.GetFileName(FullName); }
            }
            public string BaseName {
                get { return System.IO.Path.GetFileNameWithoutExtension(FullName); }
            }
            public string Extension {
                get { return System.IO.Path.GetExtension(FullName); }
            }
            public string Container {
                get { return Format; }
            }
            public string ContainerDescr {
                get { return FormatDescr; }
            }
            public double Fps {
                get { return Framerate; }
            }
            public int Kbps {
                get { return Bitrate / 1000; }
            }
            public int KbpsV {
                get { return VideoBitrate / 1000; }
            }
            public int KbpsA {
                get { return AudioBitrate / 1000; }
            }
            public double Megapixel {
                get { return (double)Width * Height / 1000000; }
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

    # Replace byte values represented by "[NNN]" and then remove non-essential chars.
    function SimpleCodecTag ([string]$s) {
        $s = ([regex]'\[(\d+)\]').replace($s, {
            param($m) [char][int]$m.groups[1].value
        })
        $s -replace '[^a-z0-9-]',''
    }

    function SimplifyFormatName ([string]$s) {
        $s  -replace 'matroska,webm','mkv' `
            -replace 'mov,mp4,m4a,3gp,3g2,mj2','mov' `
            -replace 'hls,applehttp','hls'
    }

    $inputItems = [System.Collections.ArrayList]@()

    function TryGet ($Object, $Property, $Default = $null) {
        try {
            $Object.$Property
        } catch [System.Management.Automation.PropertyNotFoundException] {
            $Default
        }
    }

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
        $vctag = $video.codec_tag_string
        $actag = if ($audio) { $audio.codec_tag_string } else { '' }
        $br_v = TryGet $video bit_rate -1
        $br_a = if ($audio) { TryGet $audio bit_rate -1 } else { $null }

        [VideoInfo]::new(
            (SimplifyFormatName $format.format_name),
            $format.format_name,
            $format.format_long_name,
            (GetStreamTypesCount $info.streams),
            [int]$video.width,
            [int]$video.height,
            [double]$format.duration,
            [int]$format.bit_rate,
            [int]$br_v,
            [int]$br_a,
            (fps_value $video.avg_frame_rate),
            $video.avg_frame_rate,
            $vcodec,
            (SimpleCodecTag $vctag),
            $vctag,
            $acodec,
            (SimpleCodecTag $actag),
            $actag,
            $channels,
            [int64]$format.size,
            $item
        )
    }

    Write-Progress @progress -Completed

}
