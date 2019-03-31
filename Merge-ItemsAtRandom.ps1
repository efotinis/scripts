<#
.SYNOPSIS
    Pick objects from a list of lists.

.DESCRIPTION
    Given a list of object lists, return items in order from each list, but
    randomly selecting a list every time, until all items and lists are exhausted.

.PARAMETER InputObject
    A array of arrays of arbitrary objects.

.EXAMPLE
    > .\Merge-ItemsAtRandom.ps1 (1,2,3),('aa','bb'),(100,200,300)
        
    1
    100
    2
    200
    3
    aa
    bb
    300

.NOTES
    Still can't figure out a meaningful name. Previous attempts:
        Get-RandomMerge
        Merge-Ordered
        Merge-ItemsAtRandom

    Similar question for C#:
        https://stackoverflow.com/questions/4577882/how-to-merge-2-sorted-listed-into-one-shuffled-list-while-keeping-internal-order
#>

param(
    [object[][]]$InputObject,
    
    [switch]$Alt
)

Set-StrictMode -Version Latest


<#

1 0 aaa
0 0 10
0 1 20
0 2 30
1 1 bbb
0 3 40
0 4 50

#>


if ($Alt) {
    Write-Error 'bad algo; this just return the first elements in a random order, then the second, etc.'
    return
    <#
    $items = [System.Collections.ArrayList]::new()
    $collIndex = 0
    foreach ($coll in $InputObject) {
        $itemIndex = 0
        foreach ($item in $coll) {
            [void]$items.Add(@(
                $collIndex
                $itemIndex
                $item
            ))
            $itemIndex += 1
        }
        $collIndex += 1
    }
    Get-Random -InputObject $items -Count $items.Count | 
        sort { $_[1] } | 
        % { "$($_[0]) $($_[1]) $($_[2])" }
    return
    #>
}

$available = [System.Collections.ArrayList]::new()

$collIndex = 0
foreach ($coll in $InputObject) {
    $collSize = $coll.Count
    if ($collSize -gt 0) {
        [void]$available.Add(@{
            index=$collIndex    # collection index in $InputObject
            size=$collSize      # size of above collection
            next=0              # index of next pending item
        })
    }
    $collIndex += 1
}

while ($available) {
    $i = Get-Random $available.Count
    $current = $available[$i]
    $InputObject[$current.index][$current.next]
    if (++$current.next -ge $current.size) {
        $available.RemoveAt($i);
    }
}


