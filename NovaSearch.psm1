Update-FormatData -AppendPath "$PSScriptRoot\NovaSearch.Format.ps1xml"


$script:NOVA_PATH = $null
$script:ENGINES_PATH = "$Env:LOCALAPPDATA\NovaSearch\engines"
$script:ENGINE_URL_TO_ID = $null


# Return "Python x.y.z" or null.
function GetPythonVersion {
    py --version 2> $null
}


# Return true if python module is installed, otherwise false.
function IsPythonModuleInstalled ([string]$Name) {
    py -c 'import nova6' 2> $null
    $LASTEXITCODE -eq 0
}


# Install Python module from PyPI.
# Caller should check $LASTEXITCODE for result.
function InstallPythonModule ([string]$Name) {
    py -m pip install nova6
}


# Check if the search engines dir exists and contains any Python files.
function CheckEnginesDir {
    $a = @(Get-Item -Path "${script:ENGINES_PATH}\*.py" 2>$null)
    $a.Count -ne 0
}


# Prompt for a Yes/No answer (default No) and return bool.
function YesNoPrompt ([string]$Caption, [string]$Message) {
    $resp = $Host.UI.PromptForChoice($Caption, $Message, @('&Yes', '&No'), 1)
    $resp -eq 0
}


# Run nova search with specified arguments. The exe is located dynamically
# and its location is cached the first time this is called.
function RunNova ([string[]]$Arguments) {
    if ($null -eq $script:NOVA_PATH) {
        $basePath = py -c 'import sys; print(sys.exec_prefix)' 2> $null
        if ($LASTEXITCODE) {
            $script:NOVA_PATH = ''
        } else {
            $script:NOVA_PATH = Join-Path -Path $basePath -ChildPath 'Scripts\nova6.exe'
        }
    }
    if (-not $script:NOVA_PATH) {
        Write-Error "Could not locate nova6.exe."
    } else {
        & $script:NOVA_PATH $Arguments
    }
}


<#
.SYNOPSIS
    Initialize environment.

.DESCRIPTION
    Checks for Python, nova6 module and search engine files.
    Prompts to download and install the latter two if needed.
#>
function Initialize-NovaSearch {
    [CmdletBinding()]
    param()

    # Python 3
    if ((GetPythonVersion) -match '^Python 3') {
        Write-Verbose 'Found Python 3.'
    } else {
        Write-Error 'Could not find Python 3.'
    }

    # nova6 module
    if (IsPythonModuleInstalled 'nova6') {
        Write-Verbose 'Found nova6 module.'
    } elseif (YesNoPrompt 'Module nova6 not found.' 'Install from PyPI?') {
        InstallPythonModule 'nova6'
        if ($LASTEXITCODE) {
            Write-Error 'Could not install module nova6.'
        }
    }

    # search engines
    $caption = "Search engines not found at $script:ENGINES_PATH."
    if (CheckEnginesDir) {
        Write-Verbose "Found search engines at $script:ENGINES_PATH."
    } elseif (YesNoPrompt $caption 'Downloaded from GitHub?') {
        $opt = @{
            Repository = 'qbittorrent/search-plugins'
            Path = 'nova3/engines'
            Destination = $script:ENGINES_PATH
        }
        Get-GitHubFolder.ps1 @opt
        if ($LASTEXITCODE) {
            Write-Error 'Could not download search engines.'
        }
    }

}


Add-Type -TypeDefinition @"
    using int64 = System.Int64;

    public struct TorrentResult
    {
        public string   Link;
        public string   Name;
        public int64    Size;
        public int      Seeds;
        public int      Leeches;
        public string   Engine;
        public string   Description;

        public TorrentResult(string link, string name, int64 size, int seeds,
            int leeches, string engine, string description)
        {
            Link = link;
            Name = name;
            Size = size;
            Seeds = seeds;
            Leeches = leeches;
            Engine = engine;
            Description = description;
        }
    }
"@


<#
.SYNOPSIS
    Get list of search engine info.

.DESCRIPTION
    Returns ID, name, base URL and list of categories of all installed
    search engines.
#>
function Get-NovaEngine {
    $args = @(
        '-d', $script:ENGINES_PATH
        '--capabilities'
    )
    $info = [xml](script:RunNova $args)
    foreach ($engine in $info.capabilities.ChildNodes) {
        [PSCustomObject]@{
            Id = $engine.LocalName
            Name = $engine.name
            Url = $engine.url
            Categories = $engine.categories -split '\s+'
        }
    }
}


if (Get-Command ConvertTo-NiceSize -ErrorAction Ignore) {
    function PrettySize ([int64]$n) {
        (ConvertTo-NiceSize $n) -replace 'B$','' -replace 'bytes?','B' -replace ' ',''
    }
} else {
    function PrettySize ([int64]$n) {
        if ($n -lt 1000) { '{0}B' -f $n }
        elseif ($n -lt 1000kb) { '{0:f0}K' -f ($n / 1kb) }
        elseif ($n -lt 1000mb) { '{0:f0}M' -f ($n / 1mb) }
        elseif ($n -lt 1000gb) { '{0:f0}G' -f ($n / 1gb) }
        elseif ($n -lt 1000tb) { '{0:f0}T' -f ($n / 1tb) }
        else { '{0:f0}P' -f ($n / 1pb) }
    }
}


function ParseInt32OrSuffixed ([string]$Text) {
    $n = 0
    if ([Int32]::TryParse($Text, [ref]$n)) {
        $n
    } else {
        try {
            ConvertFrom-NiceSize $Text
        } catch {
            Write-Error "Could not parse 32-bit integer (or suffixed float): $Text"
            0
        }
    }
}


function ParseInt64 ([string]$Text) {
    $n = 0
    if ([Int64]::TryParse($Text, [ref]$n)) {
        $n
    } else {
        Write-Error "Could not parse 64-bit integer: $Text"
        0
    }
}


<#
.SYNOPSIS
    Search torrents.

.DESCRIPTION
    Searches for torrents and returns results showing: name, size, seeds,
    leeches, torrent URL, description URL and engine ID.

.PARAMETER Keyword
    One or more search criteria.

.PARAMETER Category
    Category to search for. One of: all, movies, tv, music, games,
    anime, software, books. Default is 'all'.

.PARAMETER Engine
    ID list of engines to use. Default is 'all' meaning all available engines.

.INPUTS
    None.

.OUTPUTS
    [TorrentResult] objects.
#>
function Search-NovaTorrent {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        [string[]]$Keyword,

        [ValidateSet('all', 'movies', 'tv', 'music', 'games', 'anime',
            'software', 'books')]
        [string]$Category = 'all',

        [string[]]$Engine = 'all'
    )
    if ($null -eq $script:ENGINE_URL_TO_ID) {
        $script:ENGINE_URL_TO_ID = @{}
        foreach ($e in script:Get-NovaEngine) {
            $script:ENGINE_URL_TO_ID[$e.Url] = $e.Id
        }
    }
    $progress = @{
        Activity = 'Getting results'
    }
    $FIELDS = 7
    $novaArgs = @(
        '-d', $script:ENGINES_PATH
        $Engine -join ','
        $Category
        $Keyword
    )
    $count = 0
    script:RunNova $novaArgs | % {
        if ($_.Trim() -eq '') {
            # ignore empty results
            return  # NOTE: this does not end the pipeline
        }
        $parts = $_ -split '\|',$FIELDS
        if ($parts.Count -ne $FIELDS) {
            Write-Error "Invalid number of result fields ($($parts.Count    )): $_"
            return  # NOTE: this does not end the pipeline
        }
        $link = $parts[0]
        $name = $parts[1]
        $size = ParseInt64 $parts[2]
        $seeds = ParseInt32OrSuffixed $parts[3]
        $leeches = ParseInt32OrSuffixed $parts[4]
        $engineId = $script:ENGINE_URL_TO_ID[$parts[5]]
        $description = $parts[6]
        [TorrentResult]::new(
            $link, $name, $size, $seeds, $leeches, $engineId, $description
        )
        ++$count
        Write-Progress @progress -Status "Results: $count"
    }
    Write-Progress @progress -Completed
}


Export-ModuleMember -Function *-*
