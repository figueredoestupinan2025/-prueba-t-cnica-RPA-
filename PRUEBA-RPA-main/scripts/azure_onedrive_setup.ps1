<#
Automatiza la configuración de OneDrive (Microsoft Graph) para el proyecto PIX RPA:
- Inicia sesión en Azure (si hace falta)
- Crea App Registration + Service Principal
- Crea Client Secret
- Concede permisos Application: Files.ReadWrite.All (y Sites.ReadWrite.All opcional)
- Intenta admin consent (requiere rol de administrador global)
- Obtiene el ID del usuario de OneDrive
- Actualiza el archivo .env del proyecto

Requisitos:
- Azure CLI instalado (az --version)
- Permisos adecuados en el tenant (App Registrations y admin consent)

Uso:
- Ejecutar en PowerShell:
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  .\scripts\azure_onedrive_setup.ps1
#>

param(
  [Parameter(Mandatory=$false)][string]$AppName = "RPA-OneDrive-Uploader",
  [Parameter(Mandatory=$false)][string]$UserEmail,
  [Parameter(Mandatory=$false)][string]$TenantId
)

Write-Host "=== PIX RPA | Configuración Azure OneDrive (Graph) ===" -ForegroundColor Cyan

# Validar Azure CLI
try {
  $null = az --version
} catch {
  Write-Error "Azure CLI no está instalado. Instalar con: winget install Microsoft.AzureCLI"
  exit 1
}

# Solicitar email de usuario si no se proporcionó
if (-not $UserEmail -or [string]::IsNullOrWhiteSpace($UserEmail)) {
  $UserEmail = Read-Host "Correo del usuario con OneDrive habilitado (ej: usuario@tu-dominio.com)"
}

# Login Azure (permitir sin suscripción)
Write-Host "Iniciando sesión en Azure..." -ForegroundColor Yellow
if ($TenantId -and -not [string]::IsNullOrWhiteSpace($TenantId)) {
  az login --tenant $TenantId --allow-no-subscriptions | Out-Null
} else {
  az login --allow-no-subscriptions | Out-Null
}

# Resolver TenantId si no se indicó
if (-not $TenantId -or [string]::IsNullOrWhiteSpace($TenantId)) {
  $TenantId = az account show --query tenantId -o tsv
}
if (-not $TenantId) {
  Write-Error "No se pudo resolver el TenantId. Asegúrate de iniciar sesión en el tenant correcto."
  exit 1
}

# Crear App Registration
Write-Host "Creando App Registration: $AppName ..." -ForegroundColor Yellow
$AppId = az ad app create --display-name $AppName --sign-in-audience AzureADMyOrg --query appId -o tsv
if (-not $AppId) {
  Write-Error "No se pudo crear la aplicación. Verifica permisos en el tenant."
  exit 1
}

# Crear Service Principal
Write-Host "Creando Service Principal..." -ForegroundColor Yellow
az ad sp create --id $AppId | Out-Null

# Crear Client Secret
Write-Host "Creando Client Secret..." -ForegroundColor Yellow
$ClientSecret = az ad app credential reset --id $AppId --display-name "rpa-secret" --append --query password -o tsv
if (-not $ClientSecret) {
  Write-Error "No se pudo crear el Client Secret"
  exit 1
}

# Conceder permisos Application (Graph)
Write-Host "Agregando permisos a Microsoft Graph (Application)..." -ForegroundColor Yellow
$GraphAppId = "00000003-0000-0000-c000-000000000000"  # Microsoft Graph
az ad app permission add --id $AppId --api $GraphAppId --api-permissions Files.ReadWrite.All=Role Sites.ReadWrite.All=Role | Out-Null

# Admin consent
Write-Host "Intentando admin consent (requiere rol de administrador global)..." -ForegroundColor Yellow
$consented = $true
try {
  az ad app permission admin-consent --id $AppId | Out-Null
} catch {
  $consented = $false
  Write-Warning "No se pudo otorgar admin consent automáticamente. Concede en Azure Portal si es necesario."
}

# Obtener ID del usuario de OneDrive
Write-Host "Obteniendo ID del usuario: $UserEmail ..." -ForegroundColor Yellow
$UserId = az ad user show --id $UserEmail --query id -o tsv
if (-not $UserId) {
  Write-Warning "No se pudo resolver el ID del usuario. Verifica el correo. Continuaré sin ONEDRIVE_USER_ID."
}

# Ubicación del .env (raíz del proyecto)
$ProjectEnv = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $ProjectEnv)) {
  Write-Error ".env no encontrado en $ProjectEnv"
  exit 1
}

# Actualizar .env
Write-Host "Actualizando .env ..." -ForegroundColor Yellow
$envText = Get-Content -Raw -Path $ProjectEnv

function Set-Or-AddLine([string]$content,[string]$key,[string]$value){
  if ($content -match "(?m)^$key=") { return ($content -replace "(?m)^$key=.*$", "$key=$value") }
  else { return ($content.TrimEnd() + "`r`n$key=$value") }
}

$envText = Set-Or-AddLine $envText "AZURE_CLIENT_ID" $AppId
$envText = Set-Or-AddLine $envText "AZURE_CLIENT_SECRET" $ClientSecret
$envText = Set-Or-AddLine $envText "AZURE_TENANT_ID" $TenantId
$envText = Set-Or-AddLine $envText "ONEDRIVE_USER_EMAIL" $UserEmail
if ($UserId) { $envText = Set-Or-AddLine $envText "ONEDRIVE_USER_ID" $UserId }

Set-Content -Encoding UTF8 -Path $ProjectEnv -Value $envText

Write-Host "=== Resumen ===" -ForegroundColor Cyan
Write-Host "AppId (AZURE_CLIENT_ID): $AppId"
Write-Host "TenantId (AZURE_TENANT_ID): $TenantId"
Write-Host "ClientSecret (guardado en .env)"
Write-Host "UserEmail (ONEDRIVE_USER_EMAIL): $UserEmail"
if ($UserId) { Write-Host "UserId (ONEDRIVE_USER_ID): $UserId" }
Write-Host "Admin consent: " -NoNewline; if ($consented) { Write-Host "OK" -ForegroundColor Green } else { Write-Host "PENDIENTE" -ForegroundColor Yellow }

Write-Host "Actualización de .env completada en: $ProjectEnv" -ForegroundColor Green
Write-Host "Si admin consent quedó pendiente: Azure Portal -> Azure AD -> App registrations -> $AppName -> API permissions -> Grant admin consent" -ForegroundColor Yellow
