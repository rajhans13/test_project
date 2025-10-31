configuration ApplyWebConfig {
    param (
        [Parameter(Mandatory = $true)]
        [string] $NodeName,

        [Parameter(Mandatory = $false)]
        [string] $ReleaseVersion = "v2025.0.1"
    )

    Import-DscResource -ModuleName PSDesiredStateConfiguration

    Node $NodeName {
        File WebContentRoot {
            Ensure          = 'Present'
            Type            = 'Directory'
            DestinationPath = 'C:\\inetpub\\wwwroot'
        }

        Script DeploymentVersionTag {
            GetScript  = { @{ Result = Get-Content -Path 'C:\\inetpub\\wwwroot\\release.txt' -ErrorAction SilentlyContinue } }
            TestScript = { (Test-Path 'C:\\inetpub\\wwwroot\\release.txt') -and ((Get-Content 'C:\\inetpub\\wwwroot\\release.txt').Trim() -eq $using:ReleaseVersion) }
            SetScript  = {
                Set-Content -Path 'C:\\inetpub\\wwwroot\\release.txt' -Value $using:ReleaseVersion
            }
        }

        Script ComplianceBeacon {
            GetScript  = { @{ Result = $(Get-Date).ToString('o') } }
            TestScript = { $false }
            SetScript  = {
                $timestamp = (Get-Date).ToString('o')
                $logLine = "[$timestamp] Release=$using:ReleaseVersion Node=$env:COMPUTERNAME"
                $logPath = 'C:\\ProgramData\\PlatformOps\\dsc-compliance.log'
                New-Item -Path (Split-Path $logPath) -ItemType Directory -Force | Out-Null
                Add-Content -Path $logPath -Value $logLine
            }
        }
    }
}
