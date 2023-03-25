function ConvertFrom-CompactDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Date
    )
    process {
        [datetime]::new(
            [int]$Date.Substring(0, 4),
            [int]$Date.Substring(4, 2),
            [int]$Date.Substring(6, 2)
        )
    }
}


function ConvertTo-CompactDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [datetime]$Date
    )
    process {
        $Date.ToString('yyyyMMdd')
    }
}


# Convert from 'M/d/(yy)yy' or 'M.d.(yy)yy' to DateTime.
# 2-digit years are assumed to be 20xx.
function ConvertFrom-USDate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Date,

        [switch]$Scan  # match substring anywhere within input
    )
    begin {
        $s1 = '(\d{1,2})/(\d{1,2})/(\d{2,4})'
        $s2 = '(\d{1,2})\.(\d{1,2})\.(\d{2,4})'
        $rx = [regex]$(if ($Scan) {
            "$s1|$s2"
        } else {
            "^$s1$|^$s2$"
        })
    }
    process {
        $a = $rx.Match($Date)
        if (-not $a.Success) {
            Write-Error "No US-style date found in string: $Date"
            return
        }
        if ($a.Groups[1].Value) {
            $m, $d, $y = $a.Groups[1..3].Value
        } else {
            $m, $d, $y = $a.Groups[4..6].Value
        }
        $y, $m, $d = @($y, $m, $d).ForEach([int])
        if ($y -lt 100) {
            $y += 2000
        }
        [datetime]::new($y, $m, $d)
    }
}


function Get-DateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [datetime]$Date,

        [Parameter(Mandatory)]
        [ValidateSet('Year', 'Quarter', 'Month')]
        [string]$Type
    )
    process {
        switch ($Type) {
            'Year' {
                $Date.ToString('yyyy')
            }
            'Quarter' {
                $y = $Date.Year
                $m = $Date.Month
                $q = [int]([System.Math]::Truncate(($m - 1) / 3) + 1)
                '{0:D4}-Q{1}' -f $y,$q
            }
            'Month' {
                $Date.ToString('yyyy-MM')
            }
            default {
                Write-Error "Unexpected date section type: $Type."
            }
        }
    }
}


function ConvertFrom-DateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                $y = [int]$Matches[1]
                [datetime]::new($y, 1, 1)
            }
            '^(\d\d\d\d)-Q(\d)$' {
                $y = [int]$Matches[1]
                $q = [int]$Matches[2]
                $m = ($q - 1) * 3 + 1
                [datetime]::new($y, $m, 1)
            }
            '^(\d\d\d\d)-(\d\d)$' {
                $y = [int]$Matches[1]
                $m = [int]$Matches[2]
                [datetime]::new($y, $m, 1)
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


function Get-NextDateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                $y = [int]$Matches[1]
                ++$y
                '{0:D4}' -f $y
            }
            '^(\d\d\d\d)-Q(\d)$' {
                $y = [int]$Matches[1]
                $q = [int]$Matches[2]
                if (++$q -gt 4) {
                    $q = 1
                    ++$y
                }
                '{0:D4}-Q{1}' -f $y,$q
            }
            '^(\d\d\d\d)-(\d\d)$' {
                $y = [int]$Matches[1]
                $m = [int]$Matches[2]
                if (++$m -gt 12) {
                    $m = 1
                    ++$y
                }
                '{0:D4}-{1:D2}' -f $y,$m
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


function Get-PreviousDateSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                $y = [int]$Matches[1]
                --$y
                '{0:D4}' -f $y
            }
            '^(\d\d\d\d)-Q(\d)$' {
                $y = [int]$Matches[1]
                $q = [int]$Matches[2]
                if (--$q -lt 1) {
                    $q = 4
                    --$y
                }
                '{0:D4}-Q{1}' -f $y,$q
            }
            '^(\d\d\d\d)-(\d\d)$' {
                $y = [int]$Matches[1]
                $m = [int]$Matches[2]
                if (--$m -lt 1) {
                    $m = 12
                    --$y
                }
                '{0:D4}-{1:D2}' -f $y,$m
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


function Get-DateSectionType {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Section
    )
    process {
        switch -regex ($Section) {
            '^(\d\d\d\d)$' {
                'Year'
            }
            '^(\d\d\d\d)-Q(\d)$' {
                'Quarter'
            }
            '^(\d\d\d\d)-(\d\d)$' {
                'Month'
            }
            default {
                Write-Error "Unexpected date section value: $Section."
            }
        }
    }
}


function Get-DateSectionRange {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$From,

        [Parameter(Mandatory)]
        [string]$To
    )
    $t1 = Get-DateSectionType $From
    if (-not $t1) {
        return
    }
    $t2 = Get-DateSectionType $To
    if (-not $t2) {
        return
    }
    if ($t1 -ne $t2) {
        Write-Error "Range sections have different types: $t1, $t2."
        return
    }
    if ($From -le $To) {
        do {
            Write-Output $From
            $From = Get-NextDateSection $From
        } while ($From -le $To)
    } else {
        do {
            Write-Output $From
            $From = Get-PreviousDateSection $From
        } while ($From -ge $To)
    }
}


Export-ModuleMember -Function *-*
