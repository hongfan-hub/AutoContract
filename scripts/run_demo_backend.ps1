param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8001
)

Set-Location $PSScriptRoot\..\examples\demo_backend
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn app.main:app --host $HostName --port $Port
