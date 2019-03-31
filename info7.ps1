# Get archive item info.
#
# Converts 7-Zip's technical listing output to PSCustomObjects.

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
                $cur = @{}
            }
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
