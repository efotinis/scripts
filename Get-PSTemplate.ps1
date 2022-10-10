<#
.SYNOPSIS
    Output various PowerShell code templates.

.DESCRIPTION
    ...

.PARAMETER CommentHelp
    Template for comment-based help.

.PARAMETER CmdletBinding
    Template for cmdlet binding attribute.

.PARAMETER NativeType
    Type name of native type template.

.PARAMETER Member
    One of more native type members. Can be a simple name or a name and type,
    separated by a colon.

.PARAMETER Full
    Output templates with all (or most) available features present. By default,
    only the most commonly used features are output.

.INPUTS
    Nothing

.OUTPUTS
    Text
#>

[CmdletBinding()]
param(
    [Parameter(ParameterSetName='CommentHelp')]
    [switch]$CommentHelp,
    
    [Parameter(ParameterSetName='CmdletBinding')]
    [switch]$CmdletBinding,
    
    [Parameter(ParameterSetName='NativeType')]
    [string]$NativeType,
    
    [Parameter(ParameterSetName='NativeType')]
    [string[]]$Member,
    
    [switch]$Full
)

# -------- comment-based help --------

$CMTHELP_SIMPLE = @'
<#
.SYNOPSIS
.DESCRIPTION
.PARAMETER
.INPUTS
.OUTPUTS
#>
'@

$CMTHELP_FULL = @'
<#
.SYNOPSIS
.DESCRIPTION
.PARAMETER
.EXAMPLE
.INPUTS
.OUTPUTS
.NOTES
.LINK
.COMPONENT
.FUNCTIONALITY
.FORWARDHELPTARGETNAME
.FORWARDHELPCATEGORY
.REMOTEHELPRUNSPACE
.EXTERNALHELP
#>
'@

# -------- cmdlet binding --------

$CMDBIND_SIMPLE = @'
[CmdletBinding(DefaultParameterSetName='…',]
param()
'@

$CMDBIND_FULL = @'
[CmdletBinding(
    ConfirmImpact='Medium',
    DefaultParameterSetName='…',
    HelpURI='…',
    SupportsPaging,
    SupportsShouldProcess,
    PositionalBinding)]
param(
)
'@

# -------- * --------

switch ($PSCmdlet.ParameterSetName) {

    'CommentHelp' {
        if ($Full) {
            echo $CMTHELP_FULL
        } else {
            echo $CMTHELP_SIMPLE
        }
    }

    'CmdletBinding' {
        if ($Full) {
            echo $CMDBIND_FULL
        } else {
            echo $CMDBIND_SIMPLE
        }
    }
    
    'NativeType' {
        echo "public class $NativeType {"
        foreach ($m in $Member) {
            $name, $type = $m -split ':',2
            echo "    public $type $name;"
        }
        echo "}"
    }

}
