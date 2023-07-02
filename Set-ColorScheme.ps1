#requires -Modules ColorUtil

<#
.SYNOPSIS
    Set various console colors to a named scheme.

.DESCRIPTION
    Sets color attributes of various console aspects to predefined schemes.

    Currently includes stream colors and PSReadLine colors.

.PARAMETER Name
    Name of color scheme to apply. Supported values:
        - Light
        - Dark
        - Default

.INPUTS
    None

.OUTPUTS
    None
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Default', 'Light', 'Dark')]
    [string]$Name
)


$DEFAULT = @{
    Console = @{
        Output = 'w/n'
        Error = 'm+/n'
        Warning = 'y+/n'
        Debug = 'c+/n'
        Verbose = 'g+/n'
    }
    ReadLine = @{
        Command = 'y+'
        Comment = 'g'
        ContinuationPrompt = 'w'
        #DefaultToken = 'w'
        Emphasis = 'c+'
        Error = 'r+'
        InlinePrediction = '#238'
        Keyword = 'g+'
        ListPrediction = 'y'
        ListPredictionSelected = '/#238'
        Member = 'w+'
        Number = 'w+'
        Operator = 'n+'
        Parameter = 'n+'
        Selection = 'n/w'
        String = 'c'
        Type = 'w'
        Variable = 'g+'
    }
}

$DARK = @{
    Console = @{
        Output = 'w/n'
        Error = 'm+/n'
        Warning = 'y+/n'
        Debug = 'c+/n'
        Verbose = 'g+/n'
    }
    ReadLine = @{
        Command = 'y+'
        Comment = 'm'
        ContinuationPrompt = 'w'
        #DefaultToken = 'w'
        Emphasis = 'c+'
        Error = 'r+'
        InlinePrediction = '#238'
        Keyword = 'g+'
        ListPrediction = 'y'
        ListPredictionSelected = '/#238'
        Member = 'w+'
        Number = 'w+'
        Operator = 'n+'
        Parameter = 'n+'
        Selection = 'n/w'
        String = 'c'
        Type = 'w'
        Variable = 'g+'
    }
}

$LIGHT = @{
    Console = @{
        Output = 'n/w'
        Error = 'm+/w'
        Warning = 'y+/w'
        Debug = 'c+/w'
        Verbose = 'g+/w'
    }
    ReadLine = @{
        Command = 'y/w'
        Comment = 'g+/w'
        ContinuationPrompt = 'n/w'
        #DefaultToken = 'n/w'
        Emphasis = 'c/w'
        Error = 'r/w'
        InlinePrediction = '#238/w'
        Keyword = 'g/w'
        ListPrediction = 'y+/w'
        ListPredictionSelected = '/#238'
        Member = 'w+/n'
        Number = 'w+/n'
        Operator = 'n+'
        Parameter = 'n+'
        Selection = 'n/w'
        String = 'c'
        Type = 'w'
        Variable = 'g+'
    }
}

function Apply ($Scheme) {
    $a = @{}
    foreach ($e in $Scheme.Console.GetEnumerator()) {
        $a[$e.Key + 'Spec'] = $e.Value
    }
    Set-ConsoleColor @a
    $clrs = @{}
    foreach ($e in $Scheme.ReadLine.GetEnumerator()) {
        # HACK: cast to string is required;
        # see: https://stackoverflow.com/questions/51177881/powershell-write-output-vs-return-in-functions
        $clrs[$e.Key] = [string](ConvertTo-AnsiColor $e.Value)
    }
    Set-PSReadLineOption -Colors $clrs
}


Apply (Get-Variable $Name).Value
