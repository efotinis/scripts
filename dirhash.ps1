# calculate hashes of all files recursively
# and also prints relative paths

[CmdLetBinding()]
param(
  [string[]]$Path = '.',
  [string]$Algorithm = 'sha256',
  [scriptblock]$Filter = { $true }
)

foreach ($topDir in $Path) {
    ls -rec -file $topDir | ? $Filter | Get-FileHash -Algorithm $Algorithm | % { 
        "$($_.hash) $((Resolve-Path -relative -LiteralPath $_.path).substring(2))"
    }
}
