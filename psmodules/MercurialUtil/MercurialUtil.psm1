#requires -Modules ColorUtil

function Get-LogItem {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipelineByPropertyName)]
        [Alias('FullName')]
        $InputObject
    )
    begin {
        $paths = [System.Collections.ArrayList]@()
    }
    process {
        $paths += @($InputObject)
    }
    end {
        $fields = @(
            'rev'
            'date|isodate'
            'file_adds'
            'file_dels'
            'file_mods'
        )
        $template = '{{dict({0})|json}}\n' -f @(
            $fields -join ','
        )
        function MakeItems ($a, $rev, $date, $items, $action) {
            foreach ($s in $items) {
                [PSCustomObject]@{
                    Revision = $rev
                    Date = $date
                    Action = $action
                    Path = $s
                }
            }
        }
        function ColorText ($s, $spec) {
            $beg = ConvertTo-AnsiColor $spec
            $end = ConvertTo-AnsiColor '//n'
            $beg + $s + $end
        }
        hg log $paths --templ $template | % {
            $_ | ConvertFrom-Json | % {
                <#
                [PSCustomObject]@{
                    Revision = $_.rev
                    Date = Get-Date $_.date
                    Added = $_.file_adds
                    Removed = $_.file_dels
                    Modified = $_.file_mods
                }
                #>
                $rev = $_.rev
                $date = Get-Date $_.date
                $a = @()
                $a += MakeItems $a $rev $date $_.file_adds (ColorText 'Added' 'g')
                $a += MakeItems $a $rev $date $_.file_dels (ColorText 'Removed' 'r')
                $a += MakeItems $a $rev $date $_.file_mods (ColorText 'Modified' 'y')
                $a | sort Path
            }
        }
    }
}


Export-ModuleMember -Function *-*
