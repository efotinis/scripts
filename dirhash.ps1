# calculate hashes of all files recursively
# and also prints relative paths

[CmdLetBinding()]
param(
  [string[]]$Path = '.',
  [string]$Algorithm = 'sha256'
)

foreach ($topDir in $Path) {
    ls -rec -file $topDir | Get-FileHash -Algorithm $Algorithm | % { 
        "$($_.hash) $((Resolve-Path -relative -LiteralPath $_.path).substring(2))"
    }
}
