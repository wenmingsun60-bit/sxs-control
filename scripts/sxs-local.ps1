param(
    [Parameter(Mandatory=$true, Position=0)][string]$Tool,
    [Parameter(Position=1)][string]$Arguments = '{}',
    [string]$Python = 'python.exe'
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$null = $Arguments | ConvertFrom-Json
$Arguments | & $Python -X utf8 -m sxs_control call $Tool --args-stdin
exit $LASTEXITCODE

