param(
  [string]$Config = "config.toml"
)

Set-Location $PSScriptRoot\..
$env:PYTHONPATH = (Resolve-Path ".\src").Path
python -m api_guard.main --config $Config
