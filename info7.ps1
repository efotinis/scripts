# Get archive item info.
#
# Converts 7-Zip's technical listing output to PSCustomObjects.

[CmdletBinding()]
param(
    [string]$Archive
)

# Convert non-empty hashtable to PSCustomObject.
function MakeObject ($h) {
    if ($h.Count) {
        [PSCustomObject]$h
    }
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

7z l -slt $Archive | ZipInfo
