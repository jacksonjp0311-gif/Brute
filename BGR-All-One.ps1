[CmdletBinding()]
param(
    [ValidateSet('Verify','Test','Demo','UI','Reproduce','GitStatus')][string]$Action = 'Verify',
    [string]$OutputRoot = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Push-Location -LiteralPath $Root
try {
    $Python = 'python'
    $Prefix = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $Python = 'py'
        $Prefix = @('-3')
    }
    if (!(Get-Command $Python -ErrorAction SilentlyContinue)) {
        throw 'Python 3.11 or later with NumPy is required.'
    }
    Write-Host ('[BITWORK v0.90] ' + $Action + ' ' + $Root)
    if ($Action -eq 'Test') {
        & $Python @Prefix -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    }
    if ($Action -eq 'Verify') {
        & $Python @Prefix -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
        & $Python @Prefix -m scripts.verify_release
        if ($LASTEXITCODE -ne 0) { throw 'Source, audit or manifest failed.' }
    }
    if ($Action -eq 'Demo') {
        & $Python @Prefix -m scripts.demo
        if ($LASTEXITCODE -ne 0) { throw 'Demo failed.' }
    }
    if ($Action -eq 'UI') {
        Write-Host 'Read-only evidence viewer: http://127.0.0.1:8078/ui/'
        & $Python @Prefix -m http.server 8078 --bind 127.0.0.1
        if ($LASTEXITCODE -ne 0) { throw 'Local server failed.' }
    }
    if ($Action -eq 'Reproduce') {
        if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
            throw 'Specify -OutputRoot with a NEW directory path.'
        }
        $Target = [System.IO.Path]::GetFullPath((Join-Path $Root $OutputRoot))
        if (Test-Path -LiteralPath $Target) {
            throw ('Refusing to overwrite original results: ' + $Target)
        }
        & $Python @Prefix -m experiments.run_study --output $Target
        if ($LASTEXITCODE -ne 0) { throw 'Study reproduction failed.' }
        & $Python @Prefix -m experiments.independent_audit --results-dir $Target
        if ($LASTEXITCODE -ne 0) { throw 'Independent audit failed.' }
    }
    if ($Action -eq 'GitStatus') {
        if (Get-Command git -ErrorAction SilentlyContinue) {
            & git status --short --branch
            if ($LASTEXITCODE -ne 0) { throw 'Git command failed.' }
        }
        if (!(Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Host 'Git is not installed; source files are locally self-contained.'
        }
    }
}
finally {
    Pop-Location
}
