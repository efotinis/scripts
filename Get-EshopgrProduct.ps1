<#
.SYNOPSIS
    Get product listings from e-shop.gr.
.DESCRIPTION
    Uses eshopgr_json.py to generate .Net objects that can be nicely formatted.
.PARAMETER Url
    Initial product listing page.
.PARAMETER Delay
    Delay in seconds between network calls. Default is handled by
    eshopgr_json.py.
.INPUTS
    URI string.
.OUTPUTS
    Product objects.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline, Position = 0)]
    [string]$Url,

    [float]$Delay = 0.2
)
begin {
    Set-StrictMode -Version Latest

    Add-Type -TypeDefinition @"
        public struct EshopgrProduct {
            public string Name;
            public string Url;
            public string Id;
            public double Price;
            public string Discount;
            public string Type;
            public string Subtype;
            public string Manufacturer;
            public string Specifications;
            public EshopgrProduct(
                string name,
                string url,
                string id,
                double price,
                string discount,
                string type,
                string subtype,
                string manufacturer,
                string specifications)
            {
                Name = name;
                Url = url;
                Id = id;
                Price = price;
                Discount = discount;
                Type = type;
                Subtype = subtype;
                Manufacturer = manufacturer;
                Specifications = specifications;
            }
        }
"@

    Update-FormatData  -PrependPath "$Env:scripts\EshopgrProduct.Format.ps1xml"



    $args = @(
        if ($PSBoundParameters.ContainsKey('Delay')) {
            '-d', $Delay
        }
        if ($VerbosePreference -eq 'Continue') {
            '-v'
        }
    )

}
process {
    eshopgr_json.py @args $Url | % { ConvertFrom-Json $_ } | % {
        [EshopgrProduct]::new(
            $_.name,
            $_.url,
            $_.id,
            $_.price,
            $_.discount,
            $_.type,
            $_.subtype,
            $_.manufacturer,
            $_.specifications
        )
    }
}
