param(
  [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot '.env'

if (!(Test-Path -LiteralPath $configPath)) {
  throw 'Missing app/.env. Copy app/.env.example to app/.env and set GOOGLE_APP_CLIENT_ID.'
}

$config = @{}
Get-Content -LiteralPath $configPath | ForEach-Object {
  if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*?)\s*$') {
    $key = $matches[1]
    $value = $matches[2].Trim()
    if ($value.Length -ge 2 -and
        (($value.StartsWith('"') -and $value.EndsWith('"')) -or
         ($value.StartsWith("'") -and $value.EndsWith("'")))) {
      $value = $value.Substring(1, $value.Length - 2)
    }
    $config[$key] = $value
  }
}

$googleClientId = $config['GOOGLE_APP_CLIENT_ID']
if ([string]::IsNullOrWhiteSpace($googleClientId)) {
  throw 'GOOGLE_APP_CLIENT_ID is missing or empty in app/.env.'
}
if ($googleClientId -match '^YOUR_') {
  throw 'Replace the GOOGLE_APP_CLIENT_ID placeholder in app/.env with the real Web Client ID.'
}

$backendEnvPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'backend/.env'
if (Test-Path -LiteralPath $backendEnvPath) {
  $backendClientId = $null
  Get-Content -LiteralPath $backendEnvPath | ForEach-Object {
    if ($_ -match '^\s*GOOGLE_WEB_CLIENT_ID\s*=\s*(.*?)\s*$') {
      $backendClientId = $matches[1].Trim()
      if ($backendClientId.Length -ge 2 -and
          (($backendClientId.StartsWith('"') -and $backendClientId.EndsWith('"')) -or
           ($backendClientId.StartsWith("'") -and $backendClientId.EndsWith("'")))) {
        $backendClientId = $backendClientId.Substring(1, $backendClientId.Length - 2)
      }
    }
  }
  if (![string]::IsNullOrWhiteSpace($backendClientId) -and
      $googleClientId -cne $backendClientId) {
    throw 'Set GOOGLE_APP_CLIENT_ID in app/.env to the same Web Client ID as GOOGLE_WEB_CLIENT_ID in backend/.env.'
  }
}

$apiBaseUrl = $config['API_BASE_URL']
if ([string]::IsNullOrWhiteSpace($apiBaseUrl)) {
  $apiBaseUrl = 'http://127.0.0.1:8000'
}

if ($CheckOnly) {
  Write-Output 'app/.env is valid for local Web startup.'
  exit 0
}

$flutterArgs = @(
  'run',
  '-d',
  'chrome',
  '--web-hostname',
  'localhost',
  '--web-port',
  '7357',
  "--dart-define=API_BASE_URL=$apiBaseUrl",
  "--dart-define=GOOGLE_APP_CLIENT_ID=$googleClientId"
)

Push-Location $PSScriptRoot
try {
  & flutter @flutterArgs
  $flutterExitCode = $LASTEXITCODE
}
finally {
  Pop-Location
}

exit $flutterExitCode
