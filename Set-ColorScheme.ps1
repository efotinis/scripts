#requires -Modules ColorUtil

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Default', 'Light', 'Dark')]
    [string]$SchemeName
)

$DEFAULT = @{
    Console = 'w/n'
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
    Console = 'w/n'
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
    Console = 'n/w'
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
    $fg, $bg = ConvertTo-ConsoleColor $Scheme.Console
    if ($null -ne $fg) {
        [Console]::ForegroundColor = $fg
    }
    if ($null -ne $bg) {
        [Console]::BackgroundColor = $bg
    }
    $clrs = @{}
    foreach ($e in $Scheme.ReadLine.GetEnumerator()) {
        # HACK: cast to string is required;
        # see: https://stackoverflow.com/questions/51177881/powershell-write-output-vs-return-in-functions
        $clrs[$e.Key] = [string](ConvertTo-AnsiColor $e.Value)
    }
    Set-PSReadLineOption -Colors $clrs
}


Apply (Get-Variable $SchemeName).Value