[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Command,
    
    [switch]$Simple,

    [string[]]$Parameter  # if omitted, show parameter attribute table
)


# Functions to format parameter attributes for table output.
function FmtType ([string]$s) {
    if ($s -eq 'SwitchParameter') { '-' } else { $s }
}
function FmtPInput ([string]$s) {
    if ($s -eq 'false') {
        ''
    } elseif ($s -match 'true \((.+)\)') {
        $Matches[1] `
            -replace 'ByPropertyName','PN' `
            -replace 'ByValue','V' `
            -replace '\s*,\s*',','
    } else {
        $s
    }
}
function FmtDefVal ([string]$s) {
    if ($s -in 'none','false') { '' } else { $s }
}
function FmtPosition ([string]$s) {
    if ($s -eq 'named') { '' } else { $s }
}
function FmtBool ([string]$s) {
    switch ($s) {
        'true' { return 'yes' }
        'false' { return '' }
        else { return $s }
    }
}


if ($Parameter.Count -eq 0) {
    # output table
    if ($Simple) {
        Get-Help $Command -Parameter * | Format-Table -AutoSize @(
            @{ n='type'; e={FmtType $_.type.name}; a='r' }
            'name'
            @{ n='pipe'; e={FmtPInput $_.pipelineinput} }
            @{ n='req'; e={FmtBool $_.required} }
            @{ n='pos'; e={FmtPosition $_.position} }
            @{ n='vlen'; e={FmtBool $_.variableLength} }
            @{ n='glob'; e={FmtBool $_.globbing} }
            @{ n='default'; e={FmtDefVal $_.defaultValue} }
        )
    } else {
        (Get-Help $Command).syntax.syntaxItem | % {
            $_.parameter | Format-Table -AutoSize @(
                @{ n='type'; e={FmtType $_.type.name}; a='r' }
                'name'
                @{ n='pipe'; e={FmtPInput $_.pipelineinput} }
                @{ n='req'; e={FmtBool $_.required} }
                @{ n='pos'; e={FmtPosition $_.position} }
                @{ n='vlen'; e={FmtBool $_.variableLength} }
                @{ n='glob'; e={FmtBool $_.globbing} }
                @{ n='default'; e={FmtDefVal $_.defaultValue} }
            )
        }
    }
} else {
    # output description
    foreach ($p in $Parameter) {
        Get-Help $Command -Parameter $p
    }
}
