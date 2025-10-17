<#
.SYNOPSIS
    Synchronizes users from Microsoft Entra ID into CSV or JSON output.

.DESCRIPTION
    Authenticates against Microsoft Graph using client credentials, retrieves users with optional
    group filtering, and writes the result to a file for downstream studio systems. Designed for
    hybrid M&E environments that need to map cloud identities to on-prem resources.

.PARAMETER TenantId
    Entra ID tenant ID (GUID or domain).

.PARAMETER AppId
    Application (client) ID of the Azure AD app registration.

.PARAMETER AppSecret
    Client secret associated with the app registration.

.PARAMETER GroupFilter
    Optional display name of a group. Only users who belong to this group are exported.

.PARAMETER OutputFile
    Destination file name. Defaults to users.csv.

.PARAMETER OutputFormat
    Output format: csv or json. Defaults to csv.

.EXAMPLE
    ./sync-users.ps1 -TenantId "contoso.onmicrosoft.com" -AppId "0000..." -AppSecret (Get-Content secret.txt)

.NOTES
    Author: Media IT Team
    Version: 1.0.0
    Security: Store secrets securely (Azure Key Vault, environment variables, etc.).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$TenantId,
    [Parameter(Mandatory = $true)][string]$AppId,
    [Parameter(Mandatory = $true)][string]$AppSecret,
    [string]$GroupFilter,
    [string]$OutputFile = "users.csv",
    [ValidateSet('csv', 'json')][string]$OutputFormat = 'csv'
)

$ErrorActionPreference = 'Stop'
$logPath = Join-Path -Path (Get-Location) -ChildPath 'sync-log.txt'

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'u'
    "$timestamp`t$Message" | Tee-Object -FilePath $logPath -Append
}

function Get-AccessToken {
    param(
        [string]$Tenant,
        [string]$ClientId,
        [string]$ClientSecret
    )

    $body = @{
        grant_type    = 'client_credentials'
        scope         = 'https://graph.microsoft.com/.default'
        client_id     = $ClientId
        client_secret = $ClientSecret
    }

    Invoke-RestMethod -Uri "https://login.microsoftonline.com/$Tenant/oauth2/v2.0/token" -Method Post -Body $body
}

function Get-GraphUsers {
    param(
        [string]$Token
    )

    $users = @()
    $uri = 'https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,userPrincipalName,department,jobTitle'

    do {
        $response = Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $Token" }
        $users += $response.value
        $uri = $response.'@odata.nextLink'
    } while ($uri)

    return $users
}

function Get-UserGroups {
    param(
        [string]$Token,
        [string]$UserId
    )

    $uri = "https://graph.microsoft.com/v1.0/users/$UserId/memberOf?$select=displayName"
    $response = Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $Token" }
    return $response.value | ForEach-Object { $_.displayName }
}

try {
    Write-Log 'Starting Entra ID user synchronization.'

    Import-Module Microsoft.Graph.Users -ErrorAction Stop

    $tokenResponse = Get-AccessToken -Tenant $TenantId -ClientId $AppId -ClientSecret $AppSecret
    $accessToken = $tokenResponse.access_token

    if (-not $accessToken) {
        throw 'Access token retrieval failed.'
    }

    $users = Get-GraphUsers -Token $accessToken

    if ($GroupFilter) {
        Write-Log "Filtering users by group '$GroupFilter'."
        $users = foreach ($user in $users) {
            try {
                $groups = Get-UserGroups -Token $accessToken -UserId $user.id
                if ($groups -contains $GroupFilter) {
                    $user | Add-Member -NotePropertyName groups -NotePropertyValue $groups -Force
                    $user
                }
            } catch {
                Write-Log "Failed to resolve groups for user $($user.userPrincipalName): $_"
            }
        }
    }

    $selectedUsers = $users | ForEach-Object {
        [PSCustomObject]@{
            DisplayName        = $_.displayName
            UserPrincipalName  = $_.userPrincipalName
            Mail               = $_.mail
            Department         = $_.department
            JobTitle           = $_.jobTitle
            Groups             = $_.groups -join ';'
        }
    }

    if ($OutputFormat -eq 'csv') {
        $selectedUsers | Export-Csv -Path $OutputFile -NoTypeInformation -Encoding UTF8
    } else {
        $selectedUsers | ConvertTo-Json -Depth 4 | Out-File -FilePath $OutputFile -Encoding UTF8
    }

    Write-Log "Synced $($selectedUsers.Count) users to $OutputFile."
}
catch {
    Write-Log "Error during synchronization: $_"
    throw
}
