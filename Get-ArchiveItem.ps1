<#
.SYNOPSIS
    Get archive item info.

.DESCRIPTION
    Lists archive entries info using 7-Zip's technical listing output.

.PARAMETER Path
    Input file path with optional wildcards. Use the pipeline to specify multiple items.

.PARAMETER LiteralPath
    Like Path, but without wildcard expansion.

.PARAMETER Password
    Password to use in case of encrypted archive headers.

.PARAMETER GetPassword
    Prompt interactively for password (overrides Password).

.INPUTS
    File

.OUTPUTS
    PSCustomObject
#>
[CmdletBinding(DefaultParameterSetName = 'Path')]
param(
    [Parameter(Mandatory, Position = 0, ValueFromPipeline, ValueFromPipelineByPropertyName, ParameterSetName = 'Path')]
    [SupportsWildcards()]
    [string]$Path,

    [Parameter(Mandatory, ValueFromPipelineByPropertyName, ParameterSetName = 'LiteralPath')]
    [Alias('PSPath')]
    [string]$LiteralPath,

    [object]$Password,    # [SecureString] or unspecified
    [switch]$GetPassword  # prompt for password; overrides $Password
)
begin {
    # Convert non-empty hashtable to PSCustomObject.
    function MakeObject ($h) {
        if ($h.Count) {
            [PSCustomObject]$h
        }
    }

    # Convert SecureString to plain text.
    function GetSecureStringText ([SecureString]$s) {
        [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
        )
    }

    # Convert info output from 7-Zip to PSCustomObjects.
    #
    # input (sequence of line strings):
    #   <header lines>  # ignored
    #   "----------"    # end of header
    #   item+
    # item:
    #   (key " = " value)+
    #   emptyline | END
    #
    function ZipInfo {
        begin {
            # currently in header; no info yet
            $cur = $null
        }
        process {
            if ($cur -eq $null) {
                if ($_ -eq '----------') {
                    # end of header; start property collection

                    # NOTE: We initialize with all possible fields, so that the
                    # resulting PSCustomObjects will be consistent; otherwise,
                    # combining the output from disparate archive types will cause
                    # Format-Table to only show columns from first object.

                    # TODO: check other archive types and consolidate all fields
                    $cur = @{
                        Path=$null
                        Method=$null
                        Size=$null
                        Block=$null
                        Modified=$null
                        'Packed Size'=$null
                        CRC=$null
                        Attributes=$null
                        Encrypted=$null
                    }
                }
                <#elseif ($_ -Match '^Type = (.+)$') {
                    if ($Matches[1] -ne '7z') {
                        #throw 'not a 7-Zip archive'
                        Write-Error '*** not a 7zip'
                        return
                    }
                }#>
            }
            else {
                if ($_) {
                    # parse key/value line
                    $key, $value = $_ -split ' = ',2
                    $cur[$key] = $value
                }
                else {
                    # current item completed
                    MakeObject($cur)
                    $cur = @{}
                }
            }
        }
        end {
            # generate final item
            MakeObject($cur)
        }
    }

    if ($GetPassword) {
        $Password = Read-Host 'password' -AsSecureString
    }
}
process {
    $getItemOpt = switch ($PSCmdlet.ParameterSetName) {
        'Path' { @{ Path = $Path } }
        'LiteralPath' { @{ LiteralPath = $LiteralPath } }
    }
    Get-Item @getItemOpt | ForEach {
        if ($_.PSIsContainer) {
            Write-Error "Item is a directory: $_"
        } else {
            $args = @(
                'l'
                '-slt'
                '-sccutf-8'
                if ($Password) { '-p' + (GetSecureStringText $Password) }
                $_.FullName
            )

            $enc = [Console]::OutputEncoding
            try {
                [Console]::OutputEncoding = [Text.Encoding]::UTF8
                7z @args | ZipInfo
            } finally {
                [Console]::OutputEncoding = $enc
            }
        }
    }
}
