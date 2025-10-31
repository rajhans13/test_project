[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DomainName,

    [Parameter(Mandatory)]
    [string] $BaselineVersion,

    [Parameter(Mandatory)]
    [string] $ConfigurationDataPath
)

Configuration ApplyWindows2025Baseline {
    param(
        [string] $DomainName,
        [string] $BaselineVersion,
        [string] $ConfigurationDataPath
    )

    Import-DscResource -ModuleName 'GroupPolicyDsc'

    Node $AllNodes.NodeName {
        LocalConfigurationManager {
            RebootNodeIfNeeded = $true
        }

        Script EnsureBaselineVersionTag {
            GetScript  = {
                return @{ Result = Get-ItemPropertyValue -LiteralPath 'HKLM:\Software\Contoso\Baseline' -Name 'Version' -ErrorAction SilentlyContinue }
            }
            TestScript = {
                $current = Get-ItemPropertyValue -LiteralPath 'HKLM:\Software\Contoso\Baseline' -Name 'Version' -ErrorAction SilentlyContinue
                return ($current -eq $using:BaselineVersion)
            }
            SetScript  = {
                New-Item -Path 'HKLM:\Software\Contoso' -Force | Out-Null
                New-ItemProperty -LiteralPath 'HKLM:\Software\Contoso\Baseline' -Name 'Version' -Value $using:BaselineVersion -PropertyType String -Force | Out-Null
            }
        }

        GroupPolicy ImportComputerBaseline {
            Name        = "WS2025-Computer-Baseline"
            BackupPath  = (Join-Path -Path $using:ConfigurationDataPath -ChildPath 'Computer')
            GpoId       = "{00000000-0000-0000-0000-000000000001}"
            Ensure      = 'Present'
        }

        GroupPolicy ImportUserBaseline {
            Name        = "WS2025-User-Baseline"
            BackupPath  = (Join-Path -Path $using:ConfigurationDataPath -ChildPath 'User')
            GpoId       = "{00000000-0000-0000-0000-000000000002}"
            Ensure      = 'Present'
        }
    }
}

ApplyWindows2025Baseline -DomainName $DomainName -BaselineVersion $BaselineVersion -ConfigurationDataPath $ConfigurationDataPath
Start-DscConfiguration -Path "./ApplyWindows2025Baseline" -Verbose -Wait -Force
