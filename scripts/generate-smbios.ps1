# Write user/smbios.json using the macserial binary shipped with the pinned OpenCore release.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Python = $null
foreach ($Candidate in @("python3", "python")) {
    if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
        $Python = $Candidate
        break
    }
}
if (-not $Python) {
    Write-Error "Python 3 is required."
}

& $Python "scripts/efi_build.py" "smbios" @args
exit $LASTEXITCODE
