<#
.SYNOPSIS
    Convert tabular data to objects.

.DESCRIPTION
    Converts data in tabular format into actual objects.

    The data consist of an initial header with column names and subsequent
    lines with field values. The last field always extends to the end of the
    line. Missing fields due to short line lengths are set to ''. Leading and
    trailing field whitespace is removed.

.PARAMETER InputObject
    Source text lines. Should be passed via the pipeline.

.PARAMETER AsHashtable
    Output hashtables instead of PSCustomObjects.

.INPUTS
    Text.

.OUTPUTS
    PSCustomObject or hashtable.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [string]$InputObject,

    [switch]$AsHashtable
)
begin {
    # Convert header line to Column objects.
    function ParseHeader ([string]$Text) {
        $rx = [regex]'\w+\s*'
        foreach ($m in $rx.Matches($Text)) {
            $isLast = $m.Index + $m.Length -eq $Text.Length
            [PSCustomObject]@{
                Name = $m.Value.Trim()
                Pos = $m.Index
                Len = if ($isLast) { $null } else { $m.Length }
            }
        }
    }
    # Extract column field and add to map object.
    function AddField ($Obj, $Col, [string]$Line) {
        if ($Col.Pos -ge $Line.Length) {
            $value = ''
        } elseif ($Col.Pos + $Col.Len -gt $Line.Length) {
            $value = $Line.Substring($Col.Pos)
        } else {
            $value = $Line.Substring($Col.Pos, $Col.Len)
        }
        $Obj[$Col.Name] = $value.Trim()
    }
    $lineNo = 0
    $columns = $null
}
process {
    ++$lineNo
    if ($lineNo -eq 1) {
        $columns = ParseHeader $InputObject
    } else {
        $a = [ordered]@{}
        foreach ($c in $columns) {
            AddField $a $c $InputObject
        }
        if ($AsHashtable) {
            [hashtable]$a
        } else {
            [PSCustomObject]$a
        }
    }
}
